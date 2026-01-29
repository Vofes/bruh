import discord
import pandas as pd
import dropbox
import argparse
import io
import os
from datetime import datetime, timedelta, timezone

# Handle hours argument from YAML
parser = argparse.ArgumentParser()
parser.add_argument('--hours', type=int, default=24)
args = parser.parse_args()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DROPBOX_TOKEN = os.getenv('DROPBOX_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
FILE_PATH = '/chat_logs.csv'

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    after_date = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    
    # 1. Fetch from Discord
    new_data = []
    async for msg in channel.history(after=after_date, limit=None):
        new_data.append([msg.id, msg.author.name, msg.created_at, msg.content])
    new_df = pd.DataFrame(new_data, columns=['ID', 'Author', 'Time', 'Content'])

    # 2. Sync with Dropbox
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    try:
        _, res = dbx.files_download(FILE_PATH)
        old_df = pd.read_csv(io.BytesIO(res.content), header=None, names=['ID', 'Author', 'Time', 'Content'], dtype=str)
    except:
        old_df = pd.DataFrame(columns=['ID', 'Author', 'Time', 'Content'])

    # 3. Merge & Deduplicate (Keeps unique Message IDs)
    final_df = pd.concat([old_df, new_df]).drop_duplicates(subset=['ID'], keep='last')
    final_df['Time'] = pd.to_datetime(final_df['Time'], utc=True)
    final_df = final_df.sort_values('Time')

    # 4. Upload (Headerless)
    csv_buf = io.StringIO()
    final_df.to_csv(csv_buf, index=False, header=False)
    dbx.files_upload(csv_buf.getvalue().encode(), FILE_PATH, mode=dropbox.files.WriteMode.overwrite)
    
    await client.close()

client.run(DISCORD_TOKEN)
