import discord
from discord.ext import commands
import asyncio
import os
import random
from dotenv import load_dotenv

# Load file .env
load_dotenv()

# ====================== CẤU HÌNH ======================
spam_file = "nhay.txt"
whitelist_file = "whitelist.txt"
LINES_PER_MESSAGE = 2

STATUS_NAME = "𝑫𝒂𝒏𝒏𝒚 𝑿𝒊𝒏 𝑪𝒉𝒂𝒐"

# ↓↓↓ THAY ID DISCORD CỦA BẠN VÀO ĐÂY (Owner) ↓↓↓
OWNER_ID = 1531199492811128853

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ====================== LẤY TOKEN TỪ FILE .env ======================
tokens_env = os.getenv("DISCORD_TOKENS", "")
TOKENS = [token.strip() for token in tokens_env.split(",") if token.strip()]

# ====================== BIẾN TOÀN CỤC ======================
spamming_dict = {}
spam_task_dict = {}
target_users_dict = {}

# ====================== WHITELIST ======================
def load_whitelist():
    if not os.path.exists(whitelist_file):
        with open(whitelist_file, "w", encoding="utf-8") as f:
            f.write(f"{OWNER_ID}\n")
        return [str(OWNER_ID)]

    with open(whitelist_file, "r", encoding="utf-8") as f:
        ids = [line.strip() for line in f.readlines() if line.strip().isdigit()]

    owner_str = str(OWNER_ID)
    if owner_str not in ids:
        ids.insert(0, owner_str)
        save_whitelist(ids)
    elif ids[0] != owner_str:
        ids.remove(owner_str)
        ids.insert(0, owner_str)
        save_whitelist(ids)

    return ids

def save_whitelist(ids):
    with open(whitelist_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ids) + "\n")

def is_whitelisted(user_id: int) -> bool:
    return str(user_id) in load_whitelist()

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

# ====================== TẠO FILE NẾU CHƯA CÓ ======================
if not os.path.exists(spam_file):
    with open(spam_file, "w", encoding="utf-8") as f:
        f.write("Dòng 1\nDòng 2\nDòng 3\nDòng 4\nDòng 5\nThay nội dung file này bằng nội dung bạn muốn treo\n")


async def create_bot(token):
    bot = commands.Bot(command_prefix="d!", intents=intents)

    @bot.event
    async def on_ready():
        print(f'✅ Bot đã online: {bot.user}')
        print(f'📁 File treo: {spam_file} | Số dòng/tin: {LINES_PER_MESSAGE}')
        print(f'👑 Owner ID: {OWNER_ID}')

        activity = discord.Game(name=STATUS_NAME)
        await bot.change_presence(activity=activity, status=discord.Status.online)

    async def check_permission(ctx):
        if not is_whitelisted(ctx.author.id):
            await ctx.send("❌ Bạn không có quyền sử dụng lệnh này!")
            return False
        return True

    @bot.command()
    async def treo(ctx, *users: discord.Member):
        if not await check_permission(ctx):
            return

        bot_id = bot.user.id
        if spamming_dict.get(bot_id, False):
            await ctx.send("❌ Đang treo rồi!")
            return

        if not os.path.exists(spam_file):
            await ctx.send("❌ Không tìm thấy file `nhay.txt`!")
            return

        target_users_dict[bot_id] = list(users)
        spamming_dict[bot_id] = True

        if target_users_dict[bot_id]:
            mentions = " ".join(user.mention for user in target_users_dict[bot_id])
            await ctx.send(f"🚀 **Bắt đầu treo!** ({LINES_PER_MESSAGE} dòng/tin)\nPing: {mentions}\nDùng `d!stop` để dừng.")
        else:
            await ctx.send(f"🚀 **Bắt đầu treo!** ({LINES_PER_MESSAGE} dòng/tin)\nDùng `d!stop` để dừng.")

        spam_task_dict[bot_id] = asyncio.create_task(spam_loop(ctx, bot_id))

    @bot.command()
    async def stop(ctx):
        if not await check_permission(ctx):
            return

        bot_id = bot.user.id
        if not spamming_dict.get(bot_id, False):
            await ctx.send("❌ Chưa có lệnh treo nào đang chạy!")
            return

        spamming_dict[bot_id] = False
        if spam_task_dict.get(bot_id):
            spam_task_dict[bot_id].cancel()

        target_users_dict[bot_id] = []
        await ctx.send("⛔ **Đã dừng treo!**")

    @bot.command()
    async def whitelist(ctx, action: str = None, user: discord.Member = None):
        if not is_owner(ctx.author.id):
            await ctx.send("❌ Chỉ **Owner** mới được dùng lệnh này!")
            return

        ids = load_whitelist()

        if action is None:
            await ctx.send(
                "**Hướng dẫn whitelist:**\n"
                "`d!whitelist add @user` → Thêm người\n"
                "`d!whitelist remove @user` → Xóa người\n"
                "`d!whitelist list` → Xem danh sách"
            )
            return

        action = action.lower()

        if action == "list":
            if not ids:
                await ctx.send("📋 Whitelist trống.")
                return
            text = "**📋 Danh sách Whitelist:**\n"
            for i, uid in enumerate(ids):
                mark = "👑 " if i == 0 else "• "
                text += f"{mark}`{uid}`\n"
            await ctx.send(text)
            return

        if user is None:
            await ctx.send("❌ Bạn cần tag người dùng! Ví dụ: `d!whitelist add @user`")
            return

        uid = str(user.id)

        if action == "add":
            if uid in ids:
                await ctx.send(f"⚠️ {user.mention} đã có trong whitelist rồi.")
                return
            ids.append(uid)
            save_whitelist(ids)
            await ctx.send(f"✅ Đã thêm {user.mention} vào whitelist.")

        elif action == "remove":
            if uid not in ids:
                await ctx.send(f"⚠️ {user.mention} không có trong whitelist.")
                return
            if uid == str(OWNER_ID):
                await ctx.send("❌ Không thể xóa **Owner** khỏi whitelist!")
                return
            ids.remove(uid)
            save_whitelist(ids)
            await ctx.send(f"✅ Đã xóa {user.mention} khỏi whitelist.")

        else:
            await ctx.send("❌ Hành động không hợp lệ. Dùng: `add` / `remove` / `list`")

    async def spam_loop(ctx, bot_id):
        try:
            with open(spam_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            if not lines:
                await ctx.send("❌ File `nhay.txt` trống!")
                spamming_dict[bot_id] = False
                return

            i = 0
            while spamming_dict.get(bot_id, False):
                if LINES_PER_MESSAGE == 1:
                    message = random.choice(lines)
                else:
                    chunk = []
                    for _ in range(LINES_PER_MESSAGE):
                        chunk.append(lines[i % len(lines)])
                        i += 1
                    message = "\n".join(chunk)

                if target_users_dict.get(bot_id):
                    mentions = " ".join(user.mention for user in target_users_dict[bot_id])
                    message = f"{message}\n{mentions}"

                if len(message) > 2000:
                    message = message[:1997] + "..."

                try:
                    await ctx.send(message)
                except discord.HTTPException as e:
                    if e.status == 429:
                        await asyncio.sleep(2)
                        continue
                    elif e.code == 50035:
                        print(f"⚠️ Bỏ qua tin quá dài - bot {bot.user}")
                        continue
                    else:
                        print(f"Lỗi bot {bot.user}: {e}")
                        continue

                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Lỗi treo bot {bot.user}: {e}")
        finally:
            spamming_dict[bot_id] = False
            target_users_dict[bot_id] = []
            print(f"✅ Bot {bot.user} đã dừng treo.")

    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Token lỗi: {token[:20]}... | Lỗi: {e}")


async def main():
    if not TOKENS:
        print("❌ Không tìm thấy token trong file .env!")
        print("→ Hãy tạo file .env và thêm dòng:")
        print("   DISCORD_TOKENS=token1,token2,token3")
        return

    print(f"🔑 Đã tải {len(TOKENS)} token từ file .env")
    load_whitelist()

    tasks = [create_bot(token) for token in TOKENS]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())