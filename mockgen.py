import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
import os
from faker import Faker

class Player:
    def __init__(self, mobile, last_name, other_names, promotional_consent):
        self.mobile = mobile
        self.last_name = last_name
        self.other_names = other_names
        self.promotional_consent = promotional_consent
        self.category = self.assign_category()
        
    def assign_category(self):
        rand = random.random()
        if rand < 0.2:  # 20% Highly Loyal
            return "HIGHLY_LOYAL"
        elif rand < 0.5:  # 30% Moderately Loyal
            return "MODERATELY_LOYAL"
        elif rand < 0.8:  # 30% Occasional
            return "OCCASIONAL"
        else:  # 20% Inactive
            return "INACTIVE"

class DailyDraws:
    def __init__(self, date):
        self.date = date
        # Two draws per day
        self.afternoon_draw = str(uuid.uuid4())
        self.evening_draw = str(uuid.uuid4())
        
        # Set fixed times for draws
        self.afternoon_time = date.replace(hour=14, minute=30)  # 2:30 PM
        self.evening_time = date.replace(hour=20, minute=30)    # 8:30 PM

class TicketGenerator:
    def __init__(self):
        self.prefix = "787"
        self.suffixes = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def generate_ticket_number(self):
        random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        suffix = random.choice(self.suffixes)
        return f"{self.prefix}-{random_numbers}{suffix}"

class DataGenerator:
    def __init__(self, num_players=1000, output_dir="daily_files"):
        self.fake = Faker()
        self.players = self.generate_players(num_players)
        self.ticket_generator = TicketGenerator()
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
    def generate_players(self, num_players):
        players = []
        Faker.seed(12345)  # For reproducible results
        
        for _ in range(num_players):
            # Generate Ghanaian-style names using Faker
            if random.random() < 0.7:  # 70% chance of Ghanaian name
                last_name = random.choice([
                    'Mensah', 'Osei', 'Owusu', 'Addo', 'Boateng', 'Adjei', 
                    'Amankwah', 'Kumah', 'Yeboah', 'Asante', 'Nkrumah', 'Annan',
                    'Asamoah', 'Appiah', 'Kufuor', 'Agyeman', 'Baffour', 'Danso'
                ])
                other_names = random.choice([
                    'Kwame', 'Kwesi', 'Kojo', 'Kwabena', 'Yaw', 'Kofi',
                    'Ama', 'Abena', 'Akua', 'Yaa', 'Afua', 'Afia',
                    'Emmanuel', 'Elizabeth', 'Grace', 'Samuel', 'Daniel', 'Mary'
                ])
            else:
                # Non-Ghanaian names for diversity
                last_name = self.fake.last_name()
                other_names = self.fake.first_name()
            
            mobile = f"233{random.randint(200000000, 599999999)}"
            player = Player(
                mobile=mobile,
                last_name=last_name,
                other_names=other_names,
                promotional_consent=random.choice(['Y', 'N'])
            )
            players.append(player)
        return players

    def generate_tickets_for_draw(self, player, draw_id, base_time):
        tickets = []
        if player.category == "INACTIVE":
            return tickets

        # Number of tickets based on player category
        num_tickets = {
            "HIGHLY_LOYAL": random.randint(3, 5),
            "MODERATELY_LOYAL": random.randint(2, 3),
            "OCCASIONAL": random.randint(1, 2)
        }.get(player.category, 0)

        # Spread tickets within 2 hours before draw time
        for _ in range(num_tickets):
            minutes_before = random.randint(0, 120)  # Up to 2 hours before draw
            timestamp = base_time - timedelta(minutes=minutes_before)
            
            tickets.append({
                "PLAYER_MOBILE": player.mobile,
                "DRAW_ID": draw_id,
                "PLAYER_NAME": f"{player.last_name} {player.other_names}",
                "TICKET": self.ticket_generator.generate_ticket_number(),
                "PRICE": "GHS 3.00",
                "CREATED": timestamp.strftime("%d/%m/%Y %H:%M")
            })
        return tickets

    def should_player_participate(self, player, draw_type):
        # Different participation rates for afternoon vs evening draws
        if player.category == "HIGHLY_LOYAL":
            return random.random() < (0.95 if draw_type == "evening" else 0.90)
        elif player.category == "MODERATELY_LOYAL":
            return random.random() < (0.75 if draw_type == "evening" else 0.65)
        elif player.category == "OCCASIONAL":
            return random.random() < (0.25 if draw_type == "evening" else 0.20)
        return False

    def generate_daily_file(self, date):
        """Generate a single day's worth of ticket data"""
        daily_draws = DailyDraws(date)
        daily_tickets = []
        
        # Generate tickets for afternoon draw
        for player in self.players:
            if self.should_player_participate(player, "afternoon"):
                tickets = self.generate_tickets_for_draw(
                    player, 
                    daily_draws.afternoon_draw,
                    daily_draws.afternoon_time
                )
                daily_tickets.extend(tickets)
        
        # Generate tickets for evening draw
        for player in self.players:
            if self.should_player_participate(player, "evening"):
                tickets = self.generate_tickets_for_draw(
                    player,
                    daily_draws.evening_draw,
                    daily_draws.evening_time
                )
                daily_tickets.extend(tickets)
        
        # Create and save daily DataFrame
        if daily_tickets:
            df = pd.DataFrame(daily_tickets)
            filename = f"tickets_{date.strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.output_dir, filename)
            df.to_csv(filepath, index=False)
            print(f"Generated {filepath} with {len(daily_tickets)} tickets")
            return df
        return None

    def generate_historical_data(self, num_days=60):
        """Generate daily files for the specified number of past days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=num_days)
        
        current_date = start_date
        while current_date <= end_date:
            self.generate_daily_file(current_date)
            current_date += timedelta(days=1)

# Usage example:
if __name__ == "__main__":
    generator = DataGenerator(num_players=100)
    generator.generate_historical_data(num_days=60)