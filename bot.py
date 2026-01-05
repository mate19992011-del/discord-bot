import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import random

GUILD_ID = 1457533192260288766
OWNER_IDS = [1437103076484976911]
MAX_USES = 5
RESET_HOURS = 1
ONLINE_CHANNEL_ID = 1457533984010539173
PREMIUM_ROLE_ID = 1457534066936123626
PREMIUM_LOG_CHANNEL_ID = 1457535299298136105

user_limits = {}
premium_users = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

def generate_number(ping, digits, mode_choice, type_choice):
    if type_choice == "Blatant":
        base = random.uniform(0.130, 0.164)
    elif type_choice == "Legit":
        base = random.uniform(0.010, 0.128)
    elif type_choice == "HvH":
        base = random.uniform(0.160, 0.198)
    else:
        base = 0.150
    adjustment = random.uniform(-0.002, 0.002)
    return f"{base + adjustment:.{digits}f}"

def is_owner(user_id):
    return user_id in OWNER_IDS

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Bot Online as {bot.user}")
    channel = bot.get_channel(ONLINE_CHANNEL_ID)
    if channel:
        await channel.send("Bot is now online. -# opened by kxrupt.")
    bot.loop.create_task(premium_check_loop())

async def premium_check_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now(timezone.utc)
        for user_id in list(premium_users.keys()):
            if now >= premium_users[user_id]["expires"]:
                guild = bot.get_guild(GUILD_ID)
                try:
                    member = await guild.fetch_member(user_id)
                except:
                    member = guild.get_member(user_id)
                role = guild.get_role(PREMIUM_ROLE_ID)
                if member and role:
                    await member.remove_roles(role)
                del premium_users[user_id]
                log_channel = guild.get_channel(PREMIUM_LOG_CHANNEL_ID)
                if log_channel:
                    embed = discord.Embed(
                        title="⌛ Premium Expired",
                        color=0xFF5555,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="User", value=f"<@{user_id}>", inline=False)
                    embed.add_field(name="Expired At", value=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
                    await log_channel.send(embed=embed)
        await asyncio.sleep(60)

@tree.command(name="sets", description="Generate prediction set", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    ping="Your ping",
    mode="Camlock or Target",
    type="Blatant, Legit, HvH",
    digits="Decimal places",
    xy_sets="Include X and Y?"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="Camlock", value="Camlock"),
    app_commands.Choice(name="Target", value="Target")
])
@app_commands.choices(type=[
    app_commands.Choice(name="Blatant", value="Blatant"),
    app_commands.Choice(name="Legit", value="Legit"),
    app_commands.Choice(name="HvH", value="HvH")
])
async def sets(
    interaction: discord.Interaction,
    ping: int,
    mode: app_commands.Choice[str],
    type: app_commands.Choice[str],
    digits: int = 8,
    xy_sets: bool = False
):
    if digits < 4 or ping < 0 or ping > 300:
        await interaction.response.send_message("Invalid input.", ephemeral=True)
        return
    user_id = str(interaction.user.id)
    now = datetime.now(timezone.utc)
    if user_id not in user_limits:
        user_limits[user_id] = {"count": MAX_USES, "reset": (now + timedelta(hours=RESET_HOURS)).isoformat()}
    reset_time = datetime.fromisoformat(user_limits[user_id]["reset"])
    if now >= reset_time:
        user_limits[user_id]["count"] = MAX_USES
        user_limits[user_id]["reset"] = (now + timedelta(hours=RESET_HOURS)).isoformat()
    if user_limits[user_id]["count"] <= 0:
        minutes = int((reset_time - now).total_seconds() / 60)
        await interaction.response.send_message(f"Limit reached. Try again in {minutes} minutes.", ephemeral=True)
        return
    user_limits[user_id]["count"] -= 1
    main = float(generate_number(ping, digits, mode.value, type.value))
    if "offset" in user_limits[user_id]:
        main += user_limits[user_id]["offset"]
    if "smoothness" in user_limits[user_id] and user_limits[user_id]["smoothness"] > 0:
        main = main / user_limits[user_id]["smoothness"]
    main = f"{main:.{digits}f}"
    left = user_limits[user_id]["count"]
    reset_in = int((datetime.fromisoformat(user_limits[user_id]["reset"]) - now).total_seconds() / 60)
    embed = discord.Embed(
        title="SET Result",
        description=f"Ping: {ping} | Mode: {mode.name} | Type: {type.name}",
        color=0xFFFFFF
    )
    embed.add_field(name="Main", value=main, inline=False)
    embed.add_field(name="Uses Left", value=str(left), inline=True)
    embed.add_field(name="Reset In", value=f"{reset_in} min", inline=True)
    try:
        await interaction.user.send(embed=embed)
        await interaction.response.send_message(
            f"{interaction.user.mention} Check your DMs!\n- {left} uses left. Reset in {reset_in} min.",
            ephemeral=False
        )
    except:
        await interaction.response.send_message("❌ Couldn't send DM.", ephemeral=False)

@tree.command(name="convertset", description="Convert an existing set into another type", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    original_set="Paste your original set here",
    type="Choose what type to convert to"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Blatant", value="Blatant"),
    app_commands.Choice(name="Legit", value="Legit"),
    app_commands.Choice(name="HvH", value="HvH")
])
async def convertset(
    interaction: discord.Interaction,
    original_set: str,
    type: app_commands.Choice[str]
):
    converted = f"[{type.name} Converted] {original_set}"
    try:
        await interaction.user.send(f"Here’s your converted set ({type.name}):\n{converted}")
        await interaction.response.send_message(f"{interaction.user.mention} check your DMs for the converted set.", ephemeral=False)
    except:
        await interaction.response.send_message("❌ Couldn't send DM.", ephemeral=True)

@tree.command(name="offsetgen", description="Generate air and prediction offsets", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(ping="Your ping", type="Prediction type")
@app_commands.choices(
    type=[
        app_commands.Choice(name="Legit", value="Legit"),
        app_commands.Choice(name="SemiLegit", value="SemiLegit"),
        app_commands.Choice(name="SemiBlatant", value="SemiBlatant"),
        app_commands.Choice(name="Blatant", value="Blatant"),
        app_commands.Choice(name="HVH", value="HVH")
    ]
)
async def offsetgen(interaction: discord.Interaction, ping: int, type: app_commands.Choice[str]):
    base_values = {
        "Legit": (0.0008, 0.0005),
        "SemiLegit": (0.0012, 0.0008),
        "SemiBlatant": (0.0018, 0.0012),
        "Blatant": (0.0023, 0.0017),
        "HVH": (0.0028, 0.0021)
    }
    air_base, pred_base = base_values.get(type.value, (0.0010, 0.0010))
    air_offset = round(air_base + random.uniform(-0.0002, 0.0002), 6)
    pred_offset = round(pred_base + random.uniform(-0.0002, 0.0002), 6)
    msg = f"Type: `{type.value}`\nAir Offset: `{air_offset}`\nPrediction Offset: `{pred_offset}`"
    try:
        await interaction.user.send(msg)
        await interaction.response.send_message("✅ Sent offsets to your DMs.", ephemeral=False)
    except:
        await interaction.response.send_message(msg, ephemeral=False)

@tree.command(name="smoothness", description="Get recommended smoothness value", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(mode="Legit or not")
@app_commands.choices(
    mode=[
        app_commands.Choice(name="Legit", value="legit"),
        app_commands.Choice(name="Not Legit", value="not")
    ]
)
async def smoothness(interaction: discord.Interaction, mode: app_commands.Choice[str]):
    if mode.value == "legit":
        value = round(random.uniform(0.030, 0.080), 3)
    else:
        value = round(random.uniform(0.100, 0.350), 3)
    msg = f"Smoothness for `{mode.name}` mode: `{value}`"
    try:
        await interaction.user.send(msg)
        await interaction.response.send_message("✅ Sent smoothness to your DMs.", ephemeral=True)
    except:
        await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="check_limit", description="View remaining uses", guild=discord.Object(id=GUILD_ID))
async def check_limit(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    now = datetime.now(timezone.utc)
    if user_id not in user_limits:
        user_limits[user_id] = {"count": MAX_USES, "reset": (now + timedelta(hours=RESET_HOURS)).isoformat()}
    data = user_limits[user_id]
    mins = int((datetime.fromisoformat(data["reset"]) - now).total_seconds() / 60)
    await interaction.response.send_message(f"You have {data['count']} uses left. Resets in {mins} min.", ephemeral=True)

@tree.command(name="limit_add", description="Give user premium or uses", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User", amount="Uses to add", days="Days", hours="Hours", minutes="Minutes")
async def limit_add(interaction: discord.Interaction, user: discord.User, amount: int, days: int = 0, hours: int = 0, minutes: int = 0):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    uid = str(user.id)
    now = datetime.now(timezone.utc)
    if uid not in user_limits:
        user_limits[uid] = {"count": MAX_USES, "reset": (now + timedelta(hours=RESET_HOURS)).isoformat()}
    user_limits[uid]["count"] += amount
    try:
        member = await interaction.guild.fetch_member(user.id)
    except:
        member = interaction.guild.get_member(user.id)
    role = interaction.guild.get_role(PREMIUM_ROLE_ID)
    if member and role:
        await member.add_roles(role)
    if days or hours or minutes:
        expires = now + timedelta(days=days, hours=hours, minutes=minutes)
        user_limits[uid]["reset"] = expires.isoformat()
        premium_users[user.id] = {"expires": expires}
        log_channel = interaction.guild.get_channel(PREMIUM_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="✨ Premium Granted",
                color=0xFFD700,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=user.mention, inline=False)
            embed.add_field(name="Granted By", value=interaction.user.mention, inline=False)
            embed.add_field(name="Usages Given", value=str(amount), inline=True)
            duration_str = f"{days}d {hours}h {minutes}m"
            embed.add_field(name="Duration", value=duration_str, inline=True)
            embed.add_field(name="Granted At", value=now.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.add_field(name="Expires At", value=expires.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            await log_channel.send(embed=embed)
    await interaction.response.send_message(f"{user.mention} granted {amount} uses and premium.", ephemeral=True)

@tree.command(name="limit_remove", description="Remove uses from user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User", amount="Amount to remove")
async def limit_remove(interaction: discord.Interaction, user: discord.User, amount: int):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    uid = str(user.id)
    if uid in user_limits:
        user_limits[uid]["count"] = max(0, user_limits[uid]["count"] - amount)
    await interaction.response.send_message(f"{user.mention} now has {user_limits[uid]['count']} uses.", ephemeral=True)

@tree.command(name="limit_reset", description="Reset uses + timer and remove premium", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="User to reset")
async def limit_reset(interaction: discord.Interaction, user: discord.User):
    if not is_owner(interaction.user.id):
        await interaction.response.send_message("Unauthorized.", ephemeral=True)
        return
    now = datetime.now(timezone.utc)
    user_limits[str(user.id)] = {"count": MAX_USES, "reset": (now + timedelta(hours=RESET_HOURS)).isoformat()}
    try:
        member = await interaction.guild.fetch_member(user.id)
    except:
        member = interaction.guild.get_member(user.id)
    role = interaction.guild.get_role(PREMIUM_ROLE_ID)
    if member and role:
        await member.remove_roles(role)
    if user.id in premium_users:
        del premium_users[user.id]
    await interaction.response.send_message(f"{user.mention}'s uses, timer, and premium were reset.", ephemeral=True)

bot.run("MTQ1NzUzNjU0OTIyMTgzMDc4OQ.Gn8kL9.0xXCUPZ1f6vchtq3ssgXwBSO2grqqaHRvteFAQ")