import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# ==================== (سيرفر Flask للتشغيل 24/7 على Render) ====================
app = Flask('')


@app.route('/')
def home():
  return 'Bot is online, active, and running 24/7!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = threading.Thread(target=run)
  t.start()


# ==================== (إعدادات البوت والـ Intents الأساسية) ====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # مفتاح قراءة رسائل الأوامر البادئة بـ #
intents.guilds = True

bot = commands.Bot(command_prefix='#', intents=intents)


@bot.event
async def on_ready():
  print(f'تم تسجيل الدخول بنجاح باسم: {bot.user.name} (ID: {bot.user.id})')
  print('البوت يعمل بكامل الأنظمة وجاهز للإدارة على مدار الساعة!')
  await bot.change_presence(activity=discord.Game(name='#help للأوامر'))


# دالة ذكية لإنشاء أو فحص رتبة الميوت تلقائياً وضبط صلاحياتها في كل الرومات
async def get_or_create_muted_role(guild):
  role_name = 'Muted'
  muted_role = discord.utils.get(guild.roles, name=role_name)

  if not muted_role:
    try:
      muted_role = await guild.create_role(
          name=role_name,
          color=discord.Color.from_rgb(47, 49, 54),
          reason='إنشاء رتبة الميوت الكتابي تلقائياً بواسطة البوت',
      )
      for channel in guild.channels:
        try:
          await channel.set_permissions(
              muted_role,
              send_messages=False,
              add_reactions=False,
              speak=False,
              create_public_threads=False,
              create_private_threads=False,
          )
        except Exception:
          pass
    except Exception as e:
      print(f'خطأ أثناء إنشاء رتبة الميوت: {e}')

  return muted_role


# ==================== (أوامر الإدارة والمودريشن الشاملة) ====================

# 1. أمر الميوت الفعلي (#mute)
@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute_member(ctx, member: discord.Member = None, *, reason=None):
  if not member:
    return await ctx.send(
        '❌ | **يرجى إشارة العضو المراد إعطاؤه الميوت! الاستخدام: `#mute @user'
        ' [السبب]`**'
    )
  if (
      ctx.author.top_role.position <= member.top_role.position
      and ctx.author != ctx.guild.owner
  ):
    return await ctx.send(
        '❌ | **لا يمكنك عمل ميوت لشخص رتبته أعلى منك أو مساوية لك!**'
    )
  if ctx.guild.me.top_role.position <= member.top_role.position:
    return await ctx.send(
        '❌ | **رتبتي أقل من رتبة هذا العضو، لا يمكنني إعطاؤه الميوت!**'
    )

  muted_role = await get_or_create_muted_role(ctx.guild)
  if not muted_role:
    return await ctx.send(
        '❌ | **فشل النظام في إنشاء أو العثور على رتبة الميوت!**'
    )

  try:
    await member.add_roles(muted_role, reason=reason or 'لا توجد أسباب مرفقة')
    embed = discord.Embed(
        description=(
            f'🔇 | **تم إعطاء الميوت الكتابي الفعلي بنجاح لـ {member.mention}**'
        ),
        color=discord.Color.red(),
    )
    if reason:
      embed.add_field(name='السبب:', value=reason, inline=False)
    await ctx.send(embed=embed)
  except Exception as e:
    await ctx.send(f'❌ | **حدث خطأ أثناء إعطاء الرتبة:** `{e}`')


# 2. أمر فك الميوت (#unmute)
@bot.command(name='unmute')
@commands.has_permissions(manage_roles=True)
async def unmute_member(ctx, member: discord.Member = None):
  if not member:
    return await ctx.send(
        '❌ | **يرجى إشارة العضو لفك الميوت عنه! الاستخدام: `#unmute @user`**'
    )
  muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
  if not muted_role or muted_role not in member.roles:
    return await ctx.send('❌ | **هذا العضو ليس عليه ميوت أساساً!**')

  try:
    await member.remove_roles(muted_role)
    await ctx.send(
        f'🔊 | **تم فك الميوت بنجاح عن {member.mention}، صار يقدر يحكي ويكتب'
        ' براحته.**'
    )
  except Exception as e:
    await ctx.send(f'❌ | **حدث خطأ أثناء إزالة الميوت:** `{e}`')


# 3. أمر مسح الرسائل (#clear)
@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
  if amount > 100:
    return await ctx.send(
        '❌ | **عذراً، لا يمكنك مسح أكثر من 100 رسالة دفعة واحدة!**'
    )
  deleted = await ctx.channel.purge(limit=amount + 1)
  msg = await ctx.send(f'🧹 | **تم بنجاح مسح `{len(deleted) - 1}` رسالة!**')
  await msg.delete(delay=3)


# 4. أمر الطرد (#kick)
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member = None, *, reason=None):
  if not member:
    return await ctx.send(
        '❌ | **يرجى إشارة العضو المراد طرده! الاستخدام: `#kick @user [السبب]`**'
    )
  if (
      ctx.author.top_role.position <= member.top_role.position
      and ctx.author != ctx.guild.owner
  ):
    return await ctx.send(
        '❌ | **لا يمكنك طرد شخص رتبته أعلى منك أو مساوية لك!**'
    )

  try:
    await member.kick(reason=reason)
    embed = discord.Embed(
        description=f'👢 | **تم طرد العضو {member.mention} بنجاح!**',
        color=discord.Color.orange(),
    )
    if reason:
      embed.add_field(name='السبب:', value=reason, inline=False)
    await ctx.send(embed=embed)
  except Exception as e:
    await ctx.send(f'❌ | **حدث خطأ أثناء محاولة الطرد:** `{e}`')


# 5. أمر الحظر (#ban)
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member = None, *, reason=None):
  if not member:
    return await ctx.send(
        '❌ | **يرجى إشارة العضو المراد حظره! الاستخدام: `#ban @user [السبب]`**'
    )
  if (
      ctx.author.top_role.position <= member.top_role.position
      and ctx.author != ctx.guild.owner
  ):
    return await ctx.send(
        '❌ | **لا يمكنك حظر شخص رتبته أعلى منك أو مساوية لك!**'
    )

  try:
    await member.ban(reason=reason)
    embed = discord.Embed(
        description=f'🔨 | **تم حظر العضو {member.mention} من السيرفر نهائياً!**',
        color=discord.Color.dark_red(),
    )
    if reason:
      embed.add_field(name='السبب:', value=reason, inline=False)
    await ctx.send(embed=embed)
  except Exception as e:
    await ctx.send(f'❌ | **حدث خطأ أثناء محاولة الحظر:** `{e}`')


# 6. أمر إلغاء الحظر (#unban)
@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban_member(ctx, *, member_name=None):
  if not member_name:
    return await ctx.send(
        '❌ | **يرجى كتابة اسم العضو أو الـ ID لإلغاء الحظر! الاستخدام: `#unban'
        ' username`**'
    )
  ban_entries = await ctx.guild.bans()
  for ban_entry in ban_entries:
    user = ban_entry.user
    if (
        f'{user.name}#{user.discriminator}' == member_name
        or user.name == member_name
        or str(user.id) == member_name
    ):
      await ctx.guild.unban(user)
      return await ctx.send(
          f'🔓 | **تم إلغاء الحظر بنجاح عن العضو:** `{user.name}`'
      )
  await ctx.send(
      '❌ | **لم يتم العثور على هذا الشخص في قائمة المحظورين، تأكد من الاسم أو الـ'
      ' ID بدقة!**'
  )


# 7. أمر قفل الروم (#lock)
@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx, channel: discord.TextChannel = None):
  channel = channel or ctx.channel
  overwrite = channel.overwrites_for(ctx.guild.default_role)
  if overwrite.send_messages is False:
    return await ctx.send(f'🔒 | **الروم {channel.mention} مقفلة مسبقاً!**')

  overwrite.send_messages = False
  await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
  await ctx.send(
      f'🔒 | **تم قفل الروم {channel.mention} بنجاح. ممنوع الكتابة فيها حالياً.**'
  )


# 8. أمر فتح الروم (#unlock)
@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx, channel: discord.TextChannel = None):
  channel = channel or ctx.channel
  overwrite = channel.overwrites_for(ctx.guild.default_role)
  if overwrite.send_messages is True or overwrite.send_messages is None:
    return await ctx.send(f'🔓 | **الروم {channel.mention} مفتوحة أساساً!**')

  overwrite.send_messages = True
  await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
  await ctx.send(
      f'🔓 | **تم فتح الروم {channel.mention} بنجاح. رجعت الأمور طبيعية.**'
  )


# 9. أمر الوضع البطيء (#slowmode)
@bot.command(name='slowmode', aliases=['slow'])
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
  if seconds < 0 or seconds > 21600:
    return await ctx.send(
        '❌ | **عذراً، يجب أن يكون الوقت بين 0 و 21600 ثانية!**'
    )
  await ctx.channel.edit(slowmode_delay=seconds)
  if seconds == 0:
    await ctx.send('⏱️ | **تم إيقاف الوضع البطيء في هذه الروم بنجاح.**')
  else:
    await ctx.send(
        f'⏱️ | **تم ضبط الوضع البطيء في هذه الروم على `{seconds}` ثانية.**'
    )


# 10. أمر معلومات العضو (#userinfo)
@bot.command(name='userinfo', aliases=['whois'])
async def user_info(ctx, member: discord.Member = None):
  member = member or ctx.author
  roles = [role.mention for role in member.roles[1:]]
  roles_str = ', '.join(roles) if roles else 'لا توجد رتب'

  embed = discord.Embed(
      title=f'معلومات عن: {member.name}',
      color=member.color,
      timestamp=ctx.message.created_at,
  )
  embed.set_thumbnail(url=member.display_avatar.url)
  embed.add_field(name='🆔 المعرف (ID):', value=member.id, inline=True)
  embed.add_field(name='🏷️ الاسم المستعار:', value=member.display_name, inline=True)
  embed.add_field(
      name='📅 تاريخ الانضمام للسيرفر:',
      value=member.joined_at.strftime('%Y-%m-%d %H:%M'),
      inline=False,
  )
  embed.add_field(
      name='🤖 تاريخ إنشاء الحساب:',
      value=member.created_at.strftime('%Y-%m-%d %H:%M'),
      inline=False,
  )
  embed.add_field(
      name=f'🎭 الرتب ({len(member.roles)-1}):',
      value=roles_str,
      inline=False,
  )
  await ctx.send(embed=embed)


# ==================== (نظام معالجة الأخطاء العام) ====================
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.MissingPermissions):
    await ctx.send('❌ | **ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر!**')
  elif isinstance(error, commands.MissingRequiredArgument):
    await ctx.send(
        '❌ | **هناك معلومات ناقصة في الأمر، تحقق من الطريقة الصحيحة للاستخدام!**'
    )
  elif isinstance(error, commands.CommandNotFound):
    pass


# ==================== (التشغيل النهائي) ====================
if __name__ == '__main__':
  keep_alive()
  TOKEN = os.getenv('TOKEN')
  if not TOKEN:
    print('❌ خطأ: لم يتم العثور على متغير التوكن `TOKEN` في ريندر!')
  else:
    bot.run(TOKEN)
