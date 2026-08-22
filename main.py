import os
import asyncio
import random
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEFAULT_BALANCE = int(os.getenv("DEFAULT_BALANCE", "0"))
DAILY_REWARD = int(os.getenv("DAILY_REWARD", "500"))
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")

if not TOKEN:
    raise RuntimeError("Thiếu DISCORD_TOKEN trong file .env hoặc Environment Variables")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong Environment Variables")

class NX88Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default(); intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def setup_hook(self):
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID)); self.tree.copy_global_to(guild=guild); await self.tree.sync(guild=guild)
        else: await self.tree.sync()

    async def ensure_user(self, user):
        existing = self.supabase.table("users").select("*").eq("user_id", str(user.id)).execute().data
        avatar = str(user.display_avatar.url)
        if existing:
            self.supabase.table("users").update({"username":user.display_name,"avatar":avatar,"updated_at":datetime.now(timezone.utc).isoformat()}).eq("user_id",str(user.id)).execute()
        else:
            self.supabase.table("users").insert({"user_id":str(user.id),"username":user.display_name,"avatar":avatar,"balance":DEFAULT_BALANCE}).execute()

    async def get_user(self, user):
        await self.ensure_user(user)
        data=self.supabase.table("users").select("*").eq("user_id",str(user.id)).single().execute().data
        return data

    async def update_balance(self,user,amount,mode="set"):
        row=await self.get_user(user); current=int(row.get("balance",0))
        new=amount if mode=="set" else current+amount if mode=="add" else max(0,current-amount)
        self.supabase.table("users").update({"balance":new,"updated_at":datetime.now(timezone.utc).isoformat()}).eq("user_id",str(user.id)).execute()

    async def record_game(self,user,won):
        row=await self.get_user(user)
        update={"games_played":int(row.get("games_played",0))+1,"wins":int(row.get("wins",0))+(1 if won else 0),"losses":int(row.get("losses",0))+(0 if won else 1)}
        self.supabase.table("users").update(update).eq("user_id",str(user.id)).execute()

bot = NX88Bot()

def money(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def profile_embed(user: discord.abc.User, row):
    played, wins, losses = row.get("games_played",0), row.get("wins",0), row.get("losses",0)
    rate = (wins / played * 100) if played else 0
    avatar = user.display_avatar.url
    e = discord.Embed(title=f"👤 Hồ sơ của {user.display_name}")
    e.set_thumbnail(url=avatar)
    e.add_field(name="💰 Balance", value=f"**{money(row.get('balance',0))}**", inline=True)
    e.add_field(name="🎮 Đã chơi", value=str(played), inline=True)
    e.add_field(name="🏆 Thắng", value=str(wins), inline=True)
    e.add_field(name="💀 Thua", value=str(losses), inline=True)
    e.add_field(name="📊 Tỉ lệ thắng", value=f"{rate:.1f}%", inline=True)
    e.add_field(name="🆔 User ID", value=str(user.id), inline=True)
    e.set_footer(text="NX88 Bot")
    return e

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.tree.command(name="profile", description="Xem hồ sơ, avatar và thống kê")
@app_commands.describe(user="Người muốn xem, để trống để xem bản thân")
async def profile(interaction: discord.Interaction, user: discord.User | None = None):
    await interaction.response.defer()
    target = user or interaction.user
    row = await bot.get_user(target)
    await interaction.followup.send(embed=profile_embed(target, row))

@bot.tree.command(name="stats", description="Xem thống kê trò chơi")
@app_commands.describe(user="Người muốn xem")
async def stats(interaction: discord.Interaction, user: discord.User | None = None):
    await interaction.response.defer()
    target = user or interaction.user
    row = await bot.get_user(target)
    played = row.get("games_played",0)
    rate = row.get("wins",0) / played * 100 if played else 0
    await interaction.followup.send(
        f"📊 **{target.display_name}**\n"
        f"🎮 Chơi: **{played}**\n🏆 Thắng: **{row['wins']}**\n"
        f"💀 Thua: **{row['losses']}**\n📈 Tỉ lệ thắng: **{rate:.1f}%**"
    )

balance_group = app_commands.Group(name="balance", description="Quản lý tiền")

@balance_group.command(name="check", description="Xem balance")
@app_commands.describe(user="Người muốn xem")
async def balance_check(interaction: discord.Interaction, user: discord.User | None = None):
    await interaction.response.defer()
    target = user or interaction.user
    row = await bot.get_user(target)
    await interaction.followup.send(f"💰 Balance của **{target.display_name}**: **{money(row.get('balance',0))}**")

def admin_only():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

@balance_group.command(name="set", description="Đặt số tiền của một người")
@app_commands.describe(user="Người dùng", amount="Số tiền mới")
@admin_only()
async def balance_set(interaction: discord.Interaction, user: discord.User, amount: app_commands.Range[int, 0]):
    await interaction.response.defer(ephemeral=True)
    await bot.update_balance(user, amount, "set")
    await interaction.followup.send(f"✅ Đã đặt balance của **{user.display_name}** thành **{money(amount)}**.")

@balance_group.command(name="give", description="Cộng tiền cho một người")
@app_commands.describe(user="Người dùng", amount="Số tiền cộng")
@admin_only()
async def balance_give(interaction: discord.Interaction, user: discord.User, amount: app_commands.Range[int, 1]):
    await interaction.response.defer(ephemeral=True)
    await bot.update_balance(user, amount, "add")
    row = await bot.get_user(user)
    await interaction.followup.send(f"💸 Đã cộng **{money(amount)}** cho **{user.display_name}**. Balance mới: **{money(row.get('balance',0))}**.")

@balance_group.command(name="remove", description="Trừ tiền của một người")
@app_commands.describe(user="Người dùng", amount="Số tiền trừ")
@admin_only()
async def balance_remove(interaction: discord.Interaction, user: discord.User, amount: app_commands.Range[int, 1]):
    await interaction.response.defer(ephemeral=True)
    await bot.update_balance(user, amount, "remove")
    row = await bot.get_user(user)
    await interaction.followup.send(f"➖ Đã trừ **{money(amount)}** của **{user.display_name}**. Còn: **{money(row.get('balance',0))}**.")

@balance_group.command(name="reset", description="Reset balance về 0")
@app_commands.describe(user="Người dùng")
@admin_only()
async def balance_reset(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer(ephemeral=True)
    await bot.update_balance(user, 0, "set")
    await interaction.followup.send(f"🔄 Đã reset balance của **{user.display_name}** về **0**.")

bot.tree.add_command(balance_group)

@bot.tree.command(name="daily", description="Nhận thưởng hàng ngày")
async def daily(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    row = await bot.get_user(interaction.user)
    now = datetime.now(timezone.utc)
    last_text = row.get("daily_at")
    last = datetime.fromisoformat(last_text) if last_text else None
    if last and now - last < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last); hours, rem = divmod(int(remaining.total_seconds()),3600); minutes=rem//60
        await interaction.followup.send(f"⏳ Bạn đã nhận rồi. Còn khoảng **{hours}h {minutes}m**.", ephemeral=True); return
    await bot.update_balance(interaction.user, DAILY_REWARD, "add")
    bot.supabase.table("users").update({"daily_at":now.isoformat()}).eq("user_id",str(interaction.user.id)).execute()
    await interaction.followup.send(f"🎁 Bạn nhận được **{money(DAILY_REWARD)}**!")

@bot.tree.command(name="play", description="Chơi tung đồng xu với bot")
@app_commands.describe(bet="Số tiền cược", choice="Chọn heads hoặc tails")
@app_commands.choices(choice=[
    app_commands.Choice(name="Heads", value="heads"),
    app_commands.Choice(name="Tails", value="tails"),
])
async def play(interaction: discord.Interaction, bet: app_commands.Range[int, 1], choice: app_commands.Choice[str]):
    await interaction.response.defer()
    row = await bot.get_user(interaction.user)
    if row["balance"] < bet:
        await interaction.followup.send("❌ Bạn không đủ tiền để cược.", ephemeral=True)
        return
    result = random.choice(["heads", "tails"])
    won = choice.value == result
    if won:
        await bot.update_balance(interaction.user, bet, "add")
        await bot.record_game(interaction.user, True)
        msg = f"🏆 **Bạn thắng!** Kết quả: **{result}**. Nhận **{money(bet)}**."
    else:
        await bot.update_balance(interaction.user, bet, "remove")
        await bot.record_game(interaction.user, False)
        msg = f"💀 **Bạn thua!** Kết quả: **{result}**. Mất **{money(bet)}**."
    await interaction.followup.send(msg)

@bot.tree.command(name="leaderboard", description="Xem bảng xếp hạng")
@app_commands.describe(category="Loại bảng xếp hạng")
@app_commands.choices(category=[
    app_commands.Choice(name="💰 Balance", value="balance"),
    app_commands.Choice(name="🏆 Wins", value="wins"),
    app_commands.Choice(name="🎮 Games Played", value="games_played"),
])
async def leaderboard(interaction: discord.Interaction, category: app_commands.Choice[str] | None = None):
    await interaction.response.defer()
    key = category.value if category else "balance"
    labels = {"balance":"💰 Balance", "wins":"🏆 Số trận thắng", "games_played":"🎮 Số lần chơi"}
    rows = bot.supabase.table("users").select("*").order(key, desc=True).limit(10).execute().data
    lines = []
    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"`#{i+1}`"
        try:
            user = await bot.fetch_user(row.get("user_id"))
            name = user.display_name
        except:
            name = row.get("username")
        value = money(row.get(key,0)) if key == "balance" else str(row.get(key,0))
        lines.append(f"{medal} **{name}** — {value}")
    e = discord.Embed(title=f"🏅 Leaderboard: {labels[key]}", description="\n".join(lines) or "Chưa có dữ liệu.")
    await interaction.edit_original_response(
    content=None,
    embed=e
)

@bot.tree.command(name="xocdia", description="Chơi Xóc Đĩa")
@app_commands.describe(bet="Số tiền cược", choice="Chọn Chẵn hoặc Lẻ")
@app_commands.choices(choice=[app_commands.Choice(name="⚪ Chẵn",value="even"),app_commands.Choice(name="🔴 Lẻ",value="odd")])
async def xocdia(interaction: discord.Interaction, bet: app_commands.Range[int,1], choice: app_commands.Choice[str]):
    await interaction.response.defer()
    row=await bot.get_user(interaction.user)
    if int(row.get("balance",0))<bet: await interaction.followup.send("❌ Không đủ tiền.",ephemeral=True); return
    reds=sum(random.randint(0,1) for _ in range(4)); result="odd" if reds%2 else "even"; won=result==choice.value
    await bot.update_balance(interaction.user,bet,"add" if won else "remove"); await bot.record_game(interaction.user,won)
    row=await bot.get_user(interaction.user)
    await interaction.followup.send(embed=discord.Embed(title="🎲 XÓC ĐĨA",description=f"Kết quả: **{reds} đỏ / {4-reds} trắng**\n{'🏆 Bạn thắng +' if won else '💀 Bạn thua -'}**{money(bet)}**\n💰 Số dư: **{money(row.get('balance',0))}**"))

@bot.tree.command(name="taixiu", description="Chơi Tài Xỉu")
@app_commands.describe(bet="Số tiền cược", choice="Tài hoặc Xỉu")
@app_commands.choices(choice=[app_commands.Choice(name="🔥 Tài (11-17)",value="tai"),app_commands.Choice(name="❄️ Xỉu (4-10)",value="xiu")])
async def taixiu(interaction: discord.Interaction, bet: app_commands.Range[int,1], choice: app_commands.Choice[str]):
    await interaction.response.defer()
    row=await bot.get_user(interaction.user)
    if int(row.get("balance",0))<bet: await interaction.followup.send("❌ Không đủ tiền.",ephemeral=True); return
    dice=[random.randint(1,6) for _ in range(3)]; total=sum(dice); result="tai" if total>=11 else "xiu"; won=result==choice.value
    await bot.update_balance(interaction.user,bet,"add" if won else "remove"); await bot.record_game(interaction.user,won)
    row=await bot.get_user(interaction.user)
    await interaction.followup.send(embed=discord.Embed(title="🎲 TÀI XỈU",description=f"🎲 **{' + '.join(map(str,dice))} = {total}**\nKết quả: **{'TÀI' if result=='tai' else 'XỈU'}**\n{'🏆 Thắng +' if won else '💀 Thua -'}**{money(bet)}**\n💰 Số dư: **{money(row.get('balance',0))}**"))

class HongBaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = set()

    @discord.ui.button(
        label="Nhận Hồng Bao",
        style=discord.ButtonStyle.success,
        custom_id="nx88_hongbao_claim",
        emoji=discord.PartialEmoji(name="sheep_minecraft", id=1529319196801110046, animated=True)
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.claimed:
            await interaction.response.send_message("❌ Bạn đã nhận hồng bao này rồi.", ephemeral=True)
            return

        self.claimed.add(uid)
        amount = random.randint(1000, 10000)
        try:
            await bot.update_balance(interaction.user, amount, "add")
            row = await bot.get_user(interaction.user)
        except Exception as e:
            self.claimed.discard(uid)
            await interaction.response.send_message(f"❌ Không thể nhận hồng bao: {e}", ephemeral=True)
            return

        await interaction.response.send_message(
            f"<a:sheep_minecraft:1529319196801110046> **{interaction.user.display_name}** đã nhận **{money(amount)}** xu!\n"
            f"💰 Số dư mới: **{money(int(row.get('balance', 0)))}** xu",
            ephemeral=True
        )

@bot.tree.command(name="hongbao", description="Admin tạo hồng bao cho mọi người")
@app_commands.checks.has_permissions(administrator=True)
async def hongbao(interaction: discord.Interaction):
    e = discord.Embed(
        title="🧧 HỒNG BAO NX88",
        description=(
            "🎉 **Hồng bao đã xuất hiện!**\n\n"
            "Bấm nút bên dưới để nhận một phần thưởng ngẫu nhiên.\n"
            "💰 Phần thưởng: **1.000 - 10.000 xu**\n"
            "👤 Mỗi người chỉ nhận **1 lần cho mỗi hồng bao**."
        )
    )
    e.set_footer(text=f"Tạo bởi {interaction.user.display_name} • NX88")
    await interaction.response.send_message(embed=e, view=HongBaoView())


baccarat_group = app_commands.Group(
    name="baccarat",
    description="Chơi Baccarat NX88"
)

@baccarat_group.command(
    name="cuoc",
    description="Cược Baccarat, tiền được trừ và chơi ngay"
)
@app_commands.describe(
    money="Số tiền cược",
    choice="Chọn cửa"
)
@app_commands.choices(choice=[
    app_commands.Choice(name="PLAYER", value="player"),
    app_commands.Choice(name="BANKER", value="banker"),
    app_commands.Choice(name="TIE", value="tie")
])
async def baccarat_cuoc(
    interaction: discord.Interaction,
    money: int,
    choice: app_commands.Choice[str]
):
    await interaction.response.defer()

    if money <= 0:
        await interaction.followup.send(
            "❌ Tiền cược phải lớn hơn 0.",
            ephemeral=True
        )
        return

    row = await bot.get_user(interaction.user)
    balance = int(row.get("balance", 0))

    if balance < money:
        await interaction.followup.send(
            f"❌ Không đủ tiền. Số dư: **{format_money(balance)}** xu",
            ephemeral=True
        )
        return

    # Trừ tiền cược trước
    await bot.update_balance(
        interaction.user,
        money,
        "remove"
    )

    # Tỉ lệ Baccarat gần thực tế
    # PLAYER: 44.6%
    # BANKER: 45.9%
    # TIE: 9.5%
    roll = random.random()

    if roll < 0.446:
        result = "player"
    elif roll < 0.905:
        result = "banker"
    else:
        result = "tie"

    # Tính tiền trả
    if choice.value == "player" and result == "player":
        payout = money * 2

    elif choice.value == "banker" and result == "banker":
        payout = int(money * 1.95)

    elif choice.value == "tie" and result == "tie":
        payout = money * 8

    # PLAYER/BANKER gặp TIE thì hoàn tiền cược
    elif result == "tie" and choice.value in ("player", "banker"):
        payout = money

    else:
        payout = 0

    if payout > 0:
        await bot.update_balance(
            interaction.user,
            payout,
            "add"
        )

    won = payout > money

    await bot.record_game(
        interaction.user,
        won
    )

    final_row = await bot.get_user(interaction.user)

    icon = {
        "player": "🔵",
        "banker": "🔴",
        "tie": "🟢"
    }[result]

    result_text = {
        "player": "PLAYER 🔵",
        "banker": "BANKER 🔴",
        "tie": "TIE 🟢"
    }[result]

    if payout > money:
        status = "🎉 **THẮNG!**"
    elif payout == money:
        status = "🤝 **HÒA, HOÀN TIỀN!**"
    else:
        status = "💀 **THUA!**"

    e = discord.Embed(
        title="🃏 BACCARAT NX88",
        description=(
            f"👤 Người chơi: **{interaction.user.display_name}**\n\n"
            f"💸 Cược: **{money(money)}** xu\n"
            f"🎯 Chọn: **{choice.value.upper()}**\n"
            f"{icon} Kết quả: **{result_text}**\n\n"
            f"{status}\n"
            f"🎁 Trả thưởng: **{money(payout)}** xu\n"
            f"💰 Số dư còn lại: **{money(int(final_row.get('balance', 0)))}** xu"
        )
    )

    e.set_thumbnail(
        url=interaction.user.display_avatar.url
    )

    await interaction.edit_original_response(
    content=None,
    embed=e
)


bot.tree.add_command(baccarat_group)

@bot.tree.command(name="help", description="Xem danh sách lệnh NX88 Bot")
async def help_command(interaction: discord.Interaction):
    e = discord.Embed(title="🤖 NX88 Bot Commands")
    e.add_field(name="👤 Người dùng", value="`/profile` `/stats` `/daily` `/play` `/xocdia` `/taixiu` `/leaderboard` `/balance check`", inline=False)
    e.add_field(name="🛠️ Admin", value="`/balance set` `/balance give` `/balance remove` `/balance reset` `/hongbao`", inline=False)
    e.set_footer(text="Các lệnh admin yêu cầu quyền Administrator")
    await interaction.followup.send(embed=e, ephemeral=True)

@balance_set.error
@balance_give.error
@balance_remove.error
@balance_reset.error
@hongbao.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        msg = "❌ Bạn không có quyền Administrator để dùng lệnh này."
    else:
        msg = f"❌ Lỗi: {error}"
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.followup.send(msg, ephemeral=True)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
