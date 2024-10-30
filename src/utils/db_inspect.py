from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///../lottery.db')
Session = sessionmaker(bind=engine)
session = Session()

# Then you can run various queries, for example:

# Count number of players
print("Total players:")
result = session.execute(text("SELECT COUNT(*) FROM players"))
print(result.scalar())

# Sample of player data
print("\nSample players:")
result = session.execute(text("SELECT * FROM players LIMIT 5"))
for row in result:
    print(row)

# Count metrics records
print("\nTotal metrics records:")
result = session.execute(text("SELECT COUNT(*) FROM player_metrics"))
print(result.scalar())

# Sample of metrics
print("\nSample metrics:")
result = session.execute(text("SELECT * FROM player_metrics LIMIT 5"))
for row in result:
    print(row)