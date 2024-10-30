from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import json
import os
import logging
from pathlib import Path
from ..models.db_models import Player, PlayerMetrics
from ..utils.db_manager import DatabaseManager


class DataProcessor:
    def __init__(self, state_file: str = "processor_state.json"):
        """
        Initialize the data processor.
        
        Args:
            state_file: Path to file storing processor state (draw numbers, history)
        """
        self.state_file = state_file
        self.state = self._load_state()
        # Add database initialization
        self.db = DatabaseManager()
        self.db.init_db()
        
    def _load_state(self) -> Dict:
        """Load or initialize processor state."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    # Validate state structure
                    required_keys = {'last_draw_number', 'processed_files', 
                                   'player_history', 'draw_mapping'}
                    if not all(key in state for key in required_keys):
                        print(f"Warning: State file corrupted or invalid. Creating new state.")
                        return self._initialize_state()
                    return state
            return self._initialize_state()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Error reading state file ({str(e)}). Creating new state.")
            return self._initialize_state()
    
    def _initialize_state(self) -> Dict:
        """Initialize a new state dictionary."""
        return {
            'last_draw_number': 300,  # Will start from D301
            'processed_files': [],
            'player_history': {},     # Store player participation history
            'draw_mapping': {}        # Map draw_ids to D-numbers
        }
    
    def _save_state(self):
        """Save current state to file with backup."""
        # Create backup of existing state file
        if os.path.exists(self.state_file):
            backup_file = f"{self.state_file}.bak"
            try:
                import shutil
                shutil.copy2(self.state_file, backup_file)
            except IOError as e:
                print(f"Warning: Could not create backup file ({str(e)})")
    
        # Convert all integer keys to strings before saving
        if 'player_history' in self.state:
            for player in self.state['player_history']:
                if 'participation' in self.state['player_history'][player]:
                    self.state['player_history'][player]['participation'] = {
                        str(k): v for k, v in 
                        self.state['player_history'][player]['participation'].items()
                    }
                if 'tickets' in self.state['player_history'][player]:
                    self.state['player_history'][player]['tickets'] = {
                        str(k): v for k, v in 
                        self.state['player_history'][player]['tickets'].items()
                    }
        
        if 'draw_mapping' in self.state:
            self.state['draw_mapping'] = {
                str(k): v for k, v in self.state['draw_mapping'].items()
            }
    
        # Save new state
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            print(f"Error saving state file: {str(e)}")
            if os.path.exists(f"{self.state_file}.bak"):
                print("Attempting to restore from backup...")
                import shutil
                shutil.copy2(f"{self.state_file}.bak", self.state_file)    


    def _assign_draw_numbers(self, daily_data: pd.DataFrame) -> Dict[str, int]:
        """
        Assign D-numbers to new draws.
        Returns mapping of draw_ids to D-numbers.
        """
        draw_ids = daily_data['DRAW_ID'].unique()
        draw_mapping = {}
        
        for draw_id in sorted(draw_ids):
            # Get draw times for this draw_id to determine sequence
            draw_times = pd.to_datetime(
                daily_data[daily_data['DRAW_ID'] == draw_id]['CREATED'],
                format='%d/%m/%Y %H:%M'
            )
            mean_hour = draw_times.dt.hour.mean()
            
            # Increment draw number
            self.state['last_draw_number'] += 1
            draw_number = self.state['last_draw_number']
            
            # Map draw_id to D-number
            draw_mapping[str(draw_id)] = draw_number
            self.state['draw_mapping'][str(draw_id)] = draw_number
        
        return draw_mapping

    def _calculate_e_score(self, player_mobile: str, daily_data: pd.DataFrame) -> int:
        """Calculate total tickets bought by player."""
        player_history = self.state['player_history'].get(player_mobile, {})
        # Only need to sum tickets from history since they include current tickets
        # after _update_player_history was called
        total_tickets = sum(int(v) for v in player_history.get('tickets', {}).values())
        return total_tickets        


    def _calculate_segment(self, player_mobile: str) -> str:
        """Calculate player segment (A-E) based on last 4 draw cycles."""
        player_history = self.state['player_history'].get(player_mobile, {})
        
        # Get last 8 draws (4 cycles, 2 draws per day)
        recent_draws = sorted(
            [int(d) for d in self.state['draw_mapping'].values()]
        )[-8:]
        if not recent_draws:
            return 'E'  # Default for new players
            
        # Count cycles with participation
        cycles_with_participation = 0
        for i in range(0, len(recent_draws), 2):
            cycle_draws = recent_draws[i:i+2]
            if any(str(d) in player_history.get('participation', {}) 
                  for d in cycle_draws):
                cycles_with_participation += 1
        
        # Determine segment
        if cycles_with_participation == 4:
            return 'A'
        elif cycles_with_participation == 3:
            return 'B'
        elif cycles_with_participation == 2:
            return 'C'
        elif cycles_with_participation == 1:
            return 'D'
        else:
            return 'E'

    def _calculate_gear(self, player_mobile: str) -> int:
        """Calculate gear (missed draws in last 4 cycles)."""
        player_history = self.state['player_history'].get(player_mobile, {})
        recent_draws = sorted(
            [int(d) for d in self.state['draw_mapping'].values()]
        )[-8:]
        
        if not recent_draws:
            return 4  # Default for new players
            
        # Count missed draws
        missed_draws = 0
        for draw in recent_draws:
            if str(draw) not in player_history.get('participation', {}):
                missed_draws += 1
                
        return min(4, missed_draws)  # Cap at 4

    def _update_player_history(self, daily_data: pd.DataFrame, draw_mapping: Dict[str, int]):
        """Update player participation history."""
        for player_mobile in daily_data['PLAYER_MOBILE'].unique():
            if player_mobile not in self.state['player_history']:
                self.state['player_history'][player_mobile] = {
                    'participation': {},
                    'tickets': {}
                }
            
            player_data = daily_data[daily_data['PLAYER_MOBILE'] == player_mobile]
            player_history = self.state['player_history'][player_mobile]
            
            for draw_id in player_data['DRAW_ID'].unique():
                # Convert draw_number to str explicitly when using as dict key
                draw_number = str(draw_mapping[str(draw_id)])  # Add str() here
                tickets_in_draw = len(player_data[player_data['DRAW_ID'] == draw_id])
                
                # Use string keys
                player_history['participation'][draw_number] = True
                player_history['tickets'][draw_number] = tickets_in_draw

    def _update_database(self, consolidated_df: pd.DataFrame, session):
        """Update database with consolidated data."""
        try:
            for _, row in consolidated_df.iterrows():
                # Update or create player record
                player = session.query(Player).get(row['MOBILE'])
                if not player:
                    player = Player(
                        mobile=row['MOBILE'],
                        last_name=row['LAST_NAME'],
                        other_names=row['OTHER_NAMES'],
                        promotional_consent=row['PROMOTIONAL_CONSENT'],
                        created_at=datetime.strptime(row['CREATED'], 
                                               '%d/%m/%Y %H:%M')
                    )
                    session.add(player)
                    session.flush()  # Ensure player is created before metrics
            
                # Only add draw-specific metrics
                draw_columns = [col for col in row.index if col.startswith('D')]
                for col in draw_columns:
                    draw_number = int(col[1:])  # Extract number from 'D301' etc
                    tickets_count = row[col]
                    if tickets_count > 0:  # Only add non-zero ticket counts
                        metrics = PlayerMetrics(
                            mobile=row['MOBILE'],
                            draw_number=draw_number,
                            tickets_count=tickets_count,
                            e_score=row['E-Score'],
                            segment=row['Indicative Segment'],
                            gear=row['Gear'],
                            updated_at=datetime.utcnow()
                        )
                        session.add(metrics)
            
        except Exception as e:
           logging.error(f"Database update failed: {str(e)}")
           raise        

    def process_daily_file(self, file_path: str) -> pd.DataFrame:
        """
        Process a daily file and update consolidated view.
        """
        # Read and prepare daily data
        
        daily_data = pd.read_csv(file_path)
        # Add this line to convert PLAYER_MOBILE to string
        daily_data['PLAYER_MOBILE'] = daily_data['PLAYER_MOBILE'].astype(str)
        # print("\nDEBUG INFO:")
        # print("Column types:", daily_data.dtypes)
        # print("\nSample DRAW_ID:", daily_data['DRAW_ID'].iloc[0], "Type:", type(daily_data['DRAW_ID'].iloc[0]))
        # print("\nFirst few rows of DRAW_ID:")
        # print(daily_data['DRAW_ID'].head())        

        daily_data['CREATED_DT'] = pd.to_datetime(
            daily_data['CREATED'], 
            format='%d/%m/%Y %H:%M'
        )
        
        # Check if file was already processed
        file_date = daily_data['CREATED_DT'].dt.date.iloc[0]
        if str(file_date) in self.state['processed_files']:
            raise ValueError(f"File for date {file_date} already processed")
            
        # Assign D-numbers to draws
        draw_mapping = self._assign_draw_numbers(daily_data)
        
        # Update player history
        self._update_player_history(daily_data, draw_mapping)
        
        # Create consolidated records
        consolidated_records = []
        for player_mobile in daily_data['PLAYER_MOBILE'].unique():
            player_data = daily_data[daily_data['PLAYER_MOBILE'] == player_mobile].iloc[0]
            
            player_name = player_data['PLAYER_NAME'].split()
            last_name = player_name[0]
            other_names = ' '.join(player_name[1:])
            
            # Calculate metrics
            e_score = self._calculate_e_score(player_mobile, daily_data)
            segment = self._calculate_segment(player_mobile)
            gear = self._calculate_gear(player_mobile)
            
            # Create base record
            record = {
                'LAST_NAME': last_name,
                'OTHER_NAMES': other_names,
                'MOBILE': player_mobile,
                'PROMOTIONAL_CONSENT': 'Y',  # This should come from player profile
                'CREATED': player_data['CREATED'],
                'E-Score': e_score,
                'Indicative Segment': segment,
                'Gear': gear
            }
            
            # Add draw columns
            player_history = self.state['player_history'][player_mobile]
            for d_number in range(301, self.state['last_draw_number'] + 1):
                col_name = f'D{d_number}'
                record[col_name] = player_history['tickets'].get(str(d_number), 0)
            
            consolidated_records.append(record)
        
        # Create consolidated DataFrame
        consolidated_df = pd.DataFrame(consolidated_records)
        
        # Add database update
        session = self.db.get_session()
        try:
            self._update_database(consolidated_df, session)
            session.commit()
            logging.info("Database successfully updated")
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating database: {str(e)}")
            raise
        finally:
            session.close()

        # Update state
        self.state['processed_files'].append(str(file_date))
        self._save_state()

  
        return consolidated_df

# Usage Example:
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python data_processor.py <path_to_daily_file>")
        sys.exit(1)
        
    processor = DataProcessor()
    try:
        result_df = processor.process_daily_file(sys.argv[1])
        print("\nProcessing successful!")
        print(f"Processed {len(result_df)} players")
        print("\nSample of consolidated data:")
        print(result_df.head())
        
        # Save consolidated view
        result_df.to_csv('consolidated_view.csv', index=False)
        print("\nSaved consolidated view to 'consolidated_view.csv'")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")