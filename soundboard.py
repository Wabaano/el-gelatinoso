import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import asyncio
import yt_dlp  # Import yt-dlp for YouTube downloading

# Define the intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Define the bot with command prefix '.' and the specified intents
bot = commands.Bot(command_prefix='.', intents=intents)

# Load audio files from the 'sounds' folder
def load_audio_files():
    sounds_folder = 'sounds'
    audio_files = [f for f in os.listdir(sounds_folder) if f.endswith(('.mp3', '.wav', '.ogg'))]
    return audio_files
    
@bot.command()
async def upload(ctx, url: str = None):
    # Check if the user has the "uploader" role
    role = discord.utils.get(ctx.author.roles, name="uploader")
    if not role:
        await ctx.send("You don't have permission to upload files. Only users with the 'uploader' role can use this command.")
        return

    # Check if a YouTube link is provided
    if url and ("youtube.com" in url or "youtu.be" in url):
        sounds_folder = 'sounds'
        os.makedirs(sounds_folder, exist_ok=True)  # Ensure the sounds folder exists

        # Retrieve video info to check the duration
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)  # Fetch info without downloading
                video_duration = info.get('duration', 0)  # Duration in seconds

                # Check if the video is longer than 3 seconds
                if video_duration > 3:
                    await ctx.send("The video is longer than 3 seconds, so it can't be downloaded.")
                    return

                # Define options to download the video if it's within the duration limit
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(sounds_folder, '%(title).20s.%(ext)s'),  # Limit title to 20 characters
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

                # Download the audio
                ydl.download([url])
                truncated_title = info['title'][:20]
                await ctx.send(f"Downloaded '{truncated_title}' and saved it in the sounds folder.")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
        return

    # Ensure there's an attachment in the message
    if not ctx.message.attachments:
        await ctx.send("Please attach an audio file or provide a YouTube link to upload.")
        return

    # Process each attachment
    for attachment in ctx.message.attachments:
        if attachment.filename.endswith(('.mp3', '.wav', '.ogg')):
            sounds_folder = 'sounds'
            os.makedirs(sounds_folder, exist_ok=True)
            file_path = os.path.join(sounds_folder, attachment.filename)
            
            # Save the attachment to the sounds folder
            await attachment.save(file_path)
            await ctx.send(f"Uploaded '{attachment.filename}' to the sounds folder.")
        else:
            await ctx.send(f"'{attachment.filename}' is not a supported audio format. Only .mp3, .wav, and .ogg are allowed.")


@bot.command()
async def list(ctx):
    audio_files = load_audio_files()
    if not audio_files:
        await ctx.send("No audio files found in the 'sounds' folder.")
        return

    view = View()
    for audio_file in audio_files:
        button = Button(label=audio_file, style=discord.ButtonStyle.primary)
        button.callback = lambda inter, file=audio_file: play_sound(inter, file)
        view.add_item(button)

    await ctx.send("Select a sound:", view=view)

async def play_sound(interaction, audio_file):
    if interaction.user.voice:
        channel = interaction.user.voice.channel

        if interaction.guild.voice_client is None:
            voice_client = await channel.connect()
        else:
            voice_client = interaction.guild.voice_client

        if voice_client.is_playing():
            voice_client.stop()

        audio_source = discord.FFmpegPCMAudio(f'sounds/{audio_file}')
        voice_client.play(audio_source, after=lambda e: print(f'Finished playing: {audio_file}'))

        new_view = discord.ui.View()
        for button in interaction.message.components[0].children:
            button.disabled = True
            new_view.add_item(button)

        await interaction.message.edit(view=new_view)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        final_view = discord.ui.View()
        for button in interaction.message.components[0].children:
            button.disabled = False
            final_view.add_item(button)

        await interaction.message.edit(view=final_view)
    else:
        await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)


bot.run('TOKEN HERE')
