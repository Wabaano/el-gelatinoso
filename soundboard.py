import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import asyncio  # Import asyncio for sleep

# Define the intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.voice_states = True  # Enable voice state intent

# Define the bot with command prefix '.' and the specified intents
bot = commands.Bot(command_prefix='.', intents=intents)

# Load audio files from the 'sounds' folder
def load_audio_files():
    sounds_folder = 'sounds'
    audio_files = [f for f in os.listdir(sounds_folder) if f.endswith(('.mp3', '.wav', '.ogg'))]
    return audio_files

@bot.command()
async def list(ctx):
    print("List command triggered")  # Debugging print
    audio_files = load_audio_files()
    if not audio_files:
        await ctx.send("No audio files found in the 'sounds' folder.")
        return

    # Create a view for the buttons
    view = View()

    # Create a button for each audio file
    for audio_file in audio_files:
        button = Button(label=audio_file, style=discord.ButtonStyle.primary)
        button.callback = lambda inter, file=audio_file: play_sound(inter, file)
        view.add_item(button)

    await ctx.send("Select a sound:", view=view)

async def play_sound(interaction, audio_file):
    print(f"Selected audio file: {audio_file}")  # Debugging print

    # Check if the user is in a voice channel
    if interaction.user.voice:
        channel = interaction.user.voice.channel

        # Check if the bot is already connected to a voice channel
        if interaction.guild.voice_client is None:  # If not connected
            voice_client = await channel.connect()
        else:
            voice_client = interaction.guild.voice_client  # Use existing connection

        # Check if the bot is already playing audio
        if voice_client.is_playing():
            # Optionally stop the currently playing audio
            voice_client.stop()  # Uncomment this line if you want to allow interruptions

        # Prepare the audio source
        audio_source = discord.FFmpegPCMAudio(f'sounds/{audio_file}')

        # Play the audio
        voice_client.play(audio_source, after=lambda e: print(f'Finished playing: {audio_file}'))

#        await interaction.response.send_message(f"Now playing: {audio_file}", ephemeral=True)

        # Create a new view with disabled buttons
        new_view = discord.ui.View()

        # Disable all buttons after one is pressed
        for button in interaction.message.components[0].children:
            button.disabled = True  # Disable all buttons
            new_view.add_item(button)  # Add disabled buttons to the new view

        # Update the message with the new view
        await interaction.message.edit(view=new_view)

        # Wait until the audio is done playing
        while voice_client.is_playing():
            await asyncio.sleep(1)  # Use asyncio.sleep instead of discord.utils.sleep

        # Create a new view again to re-enable buttons
        final_view = discord.ui.View()
        for button in interaction.message.components[0].children:
            button.disabled = False  # Re-enable all buttons
            final_view.add_item(button)  # Add enabled buttons to the final view

        await interaction.message.edit(view=final_view)  # Update view again
    else:
        await interaction.response.send_message("You are not connected to a voice channel.", ephemeral=True)



bot.run('TOKEN HERE OR I WILL KILL ALL YOUR FAMILY')