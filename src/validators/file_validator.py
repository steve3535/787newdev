from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from dataclasses import dataclass

@dataclass
class ValidationError:
    error_type: str
    message: str
    details: Optional[Dict] = None

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    data: Optional[pd.DataFrame] = None

class FileValidator:
    """Validates daily ticket files for the lottery system."""
    
    REQUIRED_COLUMNS = {
        'PLAYER_MOBILE': str,
        'DRAW_ID': str,
        'PLAYER_NAME': str,
        'TICKET': str,
        'PRICE': str,
        'CREATED': str
    }

    TICKET_PATTERN = r'^787-\d{9}[A-Z]$'
    MOBILE_PATTERN = r'^233\d{9}$'
    PRICE_PATTERN = r'^GHS \d+\.\d{2}$'
    
    def __init__(self):
        self.errors = []

    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Main validation method for daily ticket files.
        Returns ValidationResult with status and any errors found.
        """
        try:
            # Read CSV file with all columns as string type
            df = pd.read_csv(file_path, dtype=str)
            
            # Trim whitespace from all string columns
            for col in df.columns:
                df[col] = df[col].str.strip()
            
            # Run all validations
            self._validate_schema(df)
            if not self.errors:  # Only continue if schema is valid
                self._validate_data_types(df)
                self._validate_business_rules(df)
            
            is_valid = len(self.errors) == 0
            return ValidationResult(
                is_valid=is_valid,
                errors=self.errors,
                data=df if is_valid else None
            )

        except Exception as e:
            self.errors.append(ValidationError(
                error_type="FILE_ERROR",
                message=f"Error reading file: {str(e)}"
            ))
            return ValidationResult(is_valid=False, errors=self.errors)

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """Validate the presence and names of required columns."""
        missing_columns = set(self.REQUIRED_COLUMNS.keys()) - set(df.columns)
        if missing_columns:
            self.errors.append(ValidationError(
                error_type="SCHEMA_ERROR",
                message="Missing required columns",
                details={"missing_columns": list(missing_columns)}
            ))

    def _validate_data_types(self, df: pd.DataFrame) -> None:
        """Validate data types and formats of all columns."""
        # Check for null values
        null_counts = df.isnull().sum()
        columns_with_nulls = null_counts[null_counts > 0]
        if not columns_with_nulls.empty:
            self.errors.append(ValidationError(
                error_type="DATA_ERROR",
                message="Null values found in data",
                details={"columns": columns_with_nulls.to_dict()}
            ))

        # Validate ticket format
        invalid_tickets = df[~df['TICKET'].astype(str).str.match(self.TICKET_PATTERN)]
        if not invalid_tickets.empty:
            self.errors.append(ValidationError(
                error_type="FORMAT_ERROR",
                message="Invalid ticket number format",
                details={"invalid_tickets": invalid_tickets['TICKET'].tolist()[:5]}
            ))

        # Validate mobile number format
        invalid_mobiles = df[~df['PLAYER_MOBILE'].astype(str).str.match(self.MOBILE_PATTERN)]
        if not invalid_mobiles.empty:
            self.errors.append(ValidationError(
                error_type="FORMAT_ERROR",
                message="Invalid mobile number format",
                details={"invalid_mobiles": invalid_mobiles['PLAYER_MOBILE'].tolist()[:5]}
            ))

        # Validate price format
        invalid_prices = df[~df['PRICE'].astype(str).str.match(self.PRICE_PATTERN)]
        if not invalid_prices.empty:
            self.errors.append(ValidationError(
                error_type="FORMAT_ERROR",
                message="Invalid price format",
                details={"invalid_prices": invalid_prices['PRICE'].tolist()[:5]}
            ))

    def _validate_business_rules(self, df: pd.DataFrame) -> None:
        """Validate business rules for the daily ticket file."""
        # Convert CREATED to datetime
        try:
            df['CREATED_DT'] = pd.to_datetime(
                df['CREATED'], 
                format='%d/%m/%Y %H:%M'
            )
        except Exception as e:
            self.errors.append(ValidationError(
                error_type="DATE_FORMAT_ERROR",
                message="Invalid date format in CREATED column",
                details={"error": str(e)}
            ))
            return  # Stop further validation if dates are invalid

        # Check for duplicate tickets
        duplicate_tickets = df[df.duplicated('TICKET', keep=False)]
        if not duplicate_tickets.empty:
            self.errors.append(ValidationError(
                error_type="DUPLICATE_ERROR",
                message="Duplicate ticket numbers found",
                details={"duplicate_tickets": duplicate_tickets['TICKET'].tolist()[:5]}
            ))

        # Get the date from the first row to validate the file name matches the data
        file_date = df['CREATED_DT'].dt.date.iloc[0]
        
        # Group by DRAW_ID to check draws
        draws = df.groupby('DRAW_ID')
        if len(draws) != 2:
            self.errors.append(ValidationError(
                error_type="DRAW_ERROR",
                message=f"Invalid number of draws for date {file_date}",
                details={
                    "date": str(file_date),
                    "num_draws": len(draws),
                    "draw_ids": list(draws.groups.keys())
                }
            ))

        # For each draw, validate time windows
        for draw_id, draw_data in draws:
            draw_times = draw_data['CREATED_DT'].dt.hour
            min_time = draw_times.min()
            max_time = draw_times.max()
            
            # Check if draw times fall within expected windows
            is_afternoon = any((12 <= t <= 15) for t in draw_times)
            is_evening = any((18 <= t <= 21) for t in draw_times)
            
            if not (is_afternoon or is_evening):
                self.errors.append(ValidationError(
                    error_type="TIME_ERROR",
                    message=f"Invalid draw time window for draw {draw_id}",
                    details={
                        "draw_id": draw_id,
                        "time_range": f"{min_time}:00 - {max_time}:00"
                    }
                ))

        # Check for invalid player names
        invalid_names = df[
            (df['PLAYER_NAME'].str.len() < 3) |  # Too short
            (~df['PLAYER_NAME'].str.contains(' '))  # No space between names
        ]
        if not invalid_names.empty:
            self.errors.append(ValidationError(
                error_type="NAME_ERROR",
                message="Invalid player names found",
                details={"invalid_names": invalid_names['PLAYER_NAME'].tolist()[:5]}
            ))

# Usage Example:
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python file_validator.py <path_to_csv_file>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    validator = FileValidator()
    result = validator.validate_file(file_path)
    
    if result.is_valid:
        print("File validation successful!")
        print(f"Total records: {len(result.data)}")
        print(f"Unique players: {result.data['PLAYER_MOBILE'].nunique()}")
        print(f"Total draws: {result.data['DRAW_ID'].nunique()}")
    else:
        print("Validation errors found:")
        for error in result.errors:
            print(f"{error.error_type}: {error.message}")
            if error.details:
                print(f"Details: {error.details}")