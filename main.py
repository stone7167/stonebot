import security as sec, json, requests, bs4, re, pytz
import asyncio, disnake, aiosqlite, platform, math, cpuinfo, tempfile
import os, random, time, string, datetime, psutil, coolsms_kakao, websocket
from gtts import gTTS
from def_list import *
import yt_dlp as youtube_dl
from googletrans import Translator
from disnake import FFmpegPCMAudio
from collections import defaultdict
from importlib.metadata import version
from captcha.image import ImageCaptcha
from disnake.ext import commands, tasks
from permissions import get_permissions
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

#intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="/") #intents=intents)
token = sec.token
developer = int(sec.developer_id)

# 시작 시간 기록
start_time = datetime.now()

embedcolor = 0xff00ff
embedwarning = 0xff9900
embedsuccess = 0x00ff00
embederrorcolor = 0xff0000

cpu_info = cpuinfo.get_cpu_info()
##################################################################################################
# 데이터베이스에서 권한을 가져오는 함수
async def get_permissions(server_id: int):
    db_path = f"database/{server_id}.db"
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT 음악기능, 경제기능, 관리기능, 유틸리티기능, 주식명령어, 코인명령어, 게임명령어, 인증, 인증_문자, 인증_이메일, 채팅관리명령어, 유저관리명령어 FROM 설정") as cursor:
            row = await cursor.fetchone()
            return list(row) if row else [1] * 11  # 기본값: 모두 활성화

# 명령어 사용 권한 체크
async def check_permissions(ctx: disnake.ApplicationCommandInteraction):
    command_permissions = {
        "음악기능": (0, "음악 기능이 비활성화되어 있습니다."),
        "경제기능": (1, "경제 기능이 비활성화되어 있습니다."),
        "관리기능": (2, "관리 기능이 비활성화되어 있습니다."),
        "유틸리티기능": (3, "유틸리티 기능이 비활성화되어 있습니다."),
        "주식명령어": (4, "경제(주식) 명령어가 비활성화되어 있습니다."),
        "코인명령어": (5, "경제(코인) 명령어가 비활성화되어 있습니다."),
        "게임명령어": (6, "경제(게임) 명령어가 비활성화되어 있습니다."),
        "인증": (7, "관리(인증) 명령어가 비활성화되어 있습니다."),
        "인증_문자": (8, "관리(인증_문자) 명령어가 비활성화되어 있습니다."),
        "인증_이메일": (9, "관리(인증_이메일) 명령어가 비활성화되어 있습니다."),
        "채팅관리명령어": (10, "관리(채팅관리) 명령어가 비활성화되어 있습니다."),
        "유저관리명령어": (11, "관리(유저관리) 명령어가 비활성화되어 있습니다."),
    }

    permissions = await get_permissions(ctx.guild.id)

    command_name = ctx.data.name
    if command_name in command_permissions:
        index, error_message = command_permissions[command_name]
        if permissions[index] == 0:  # 0은 비활성화
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=error_message)
            await ctx.send(embed=embed, ephemeral=True)
            return

    return True  # 모든 권한 체크가 통과되었을 경우

# 파일 경로 설정
PATCHNOTE_FILE = os.path.join('system_database', 'patchnote.txt')
EVENT_FILE = os.path.join('system_database', 'event.txt')

# 파일에 내용을 저장하는 함수 (덮어쓰기)
def save_to_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content + "\n")

# 파일 내용을 읽어오는 함수
async def read_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.strip()  # 내용 반환 (공백 제거)
    except FileNotFoundError:
        return None

# 패치 노트를 보여주는 명령어
@bot.slash_command(name="패치노트", description="최신 패치 노트를 보여줍니다.")
async def show_patchnote(ctx: disnake.ApplicationCommandInteraction):
    if not await check_permissions(ctx):
        return
    
    patchnotes = await read_from_file(PATCHNOTE_FILE)
    
    if patchnotes is None:
        await ctx.send("패치 노트 파일을 찾을 수 없습니다.")
        return
    if not patchnotes:
        await ctx.send("현재 저장된 패치 노트가 없습니다.")
        return
    
    embed = disnake.Embed(title="패치 노트 📄", color=0x00ff00, description=patchnotes)
    await ctx.send(embed=embed)

# 패치 노트를 추가하는 명령어
@bot.slash_command(name="패치노트_업데이트", description="패치 노트를 업데이트합니다. [개발자전용]")
async def add_patchnote(ctx: disnake.CommandInteraction, note: str):
    if ctx.author.id != developer:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    save_to_file(PATCHNOTE_FILE, note)
    embed = disnake.Embed(color=embederrorcolor)
    embed.add_field(name="✅ 업데이트 완료", value=note)
    await ctx.send(embed=embed, ephemeral=True)

# 이벤트를 보여주는 명령어
@bot.slash_command(name="이벤트", description="최신 이벤트를 보여줍니다.")
async def show_event(ctx: disnake.ApplicationCommandInteraction):
    if not await check_permissions(ctx):
        return

    events = await read_from_file(EVENT_FILE)

    if events is None:
        await ctx.send("이벤트 파일을 찾을 수 없습니다.")
        return
    if not events:
        await ctx.send("현재 저장된 이벤트가 없습니다.")
        return

    embed = disnake.Embed(title="이벤트 📄", color=0x00ff00, description=events)
    await ctx.send(embed=embed)

# 이벤트를 추가하는 명령어
@bot.slash_command(name="이벤트_업데이트", description="이벤트를 업데이트합니다. [개발자전용]")
async def add_event(ctx: disnake.CommandInteraction, note: str):
    if ctx.author.id != developer:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    save_to_file(EVENT_FILE, note)
    embed = disnake.Embed(color=embederrorcolor)
    embed.add_field(name="✅ 업데이트 완료", value=note)
    await ctx.send(embed=embed, ephemeral=True)

# 지역코드
region_codes = {
    "서울특별시": "B10",
    "부산광역시": "C10",
    "대구광역시": "D10",
    "인천광역시": "E10",
    "광주광역시": "F10",
    "대전광역시": "G10",
    "울산광역시": "H10",
    "세종특별자치시": "I10",
    "경기도": "J10",
    "강원도": "K10",
    "충청북도": "M10",
    "충청남도": "N10",
    "전라북도": "P10",
    "전라남도": "Q10",
    "경상북도": "R10",
    "경상남도": "S10",
    "제주특별자치도": "T10"
}

@bot.slash_command(name='급식', description="급식 메뉴를 알려줍니다.")
async def meal(ctx: disnake.CommandInteraction, 지역=commands.Param(name="지역", description="학교가 위치한 지역을 골라주세요.", choices=list(region_codes.keys())), 학교명: str=commands.Param(name="학교명", description="학교명을 ~~학교 까지 입력해주세요."), 날짜: str=commands.Param(name="날짜", description="YYYYMMDD  8자를 입력해주세요.", default=None)):
    if not await check_permissions(ctx):
        return
    
    # 학교명 수정
    if 학교명.endswith('초') or 학교명.endswith('고'):
        학교명 += '등학교'
    elif 학교명.endswith('중'):
        학교명 += '학교'
    
    # 지역 코드 설정
    edu_office_code = region_codes[지역]
    date = 날짜 if 날짜 else datetime.now().strftime('%Y%m%d')

    await ctx.response.defer()

    try:
        # 비동기로 급식 정보 및 칼로리 정보 가져오기
        meal_info_task = get_meal_info_async(학교명, edu_office_code, date)
        calorie_info_task = get_calorie_info_async(학교명, edu_office_code, date)
        
        # 두 작업을 동시에 실행
        meal_info, meal_date = await meal_info_task
        calorie_info, _ = await calorie_info_task

        # 날짜 및 요일 처리
        meal_datetime = datetime.strptime(meal_date, '%Y%m%d')
        weekday_kor = ['월', '화', '수', '목', '금', '토', '일']
        weekday_str = weekday_kor[meal_datetime.weekday()]

        # 임베드 메시지 생성
        embed = disnake.Embed(
            title=f"{학교명}",
            description=f'날짜 : {meal_datetime.month}월 {meal_datetime.day}일 ({weekday_str})',
            color=disnake.Color(0xD3851F)
        )
        embed.add_field(name='메뉴 목록', value=f"```\n{meal_info}\n```", inline=False)

        # 칼로리 정보 처리
        if calorie_info != "칼로리 정보가 없습니다.":
            embed.set_footer(text=f'칼로리 정보: {calorie_info}')
        else:
            embed.set_footer(text=None)

        # 버튼 생성
        interaction_user_id = ctx.user.id
        이전날 = disnake.ui.Button(label="전날", style=disnake.ButtonStyle.red)
        세부사항 = disnake.ui.Button(label="▼", style=disnake.ButtonStyle.gray)
        다음날 = disnake.ui.Button(label="다음날", style=disnake.ButtonStyle.blurple)

        # 사용자 체크 함수
        async def check_user(interaction: disnake.CommandInteraction):
            if interaction.user.id != interaction_user_id:
                await interaction.followup.send_message("다른 사람의 상호작용입니다.", ephemeral=True)
                return False
            return True

        # 이전날 버튼 콜백
        async def previous_day_callback(interaction: disnake.CommandInteraction):
            nonlocal meal_date  # meal_date를 nonlocal로 선언하여 외부 변수 사용
            if not await check_user(interaction):
                return

            await interaction.followup.defer(ephemeral=False)

            previous_date = datetime.strptime(meal_date, '%Y%m%d') - timedelta(days=1)
            meal_info, meal_date = await get_meal_info_async(학교명, edu_office_code, previous_date.strftime('%Y%m%d'))
            calorie_info, _ = await get_calorie_info_async(학교명, edu_office_code, previous_date.strftime('%Y%m%d'))
            meal_info_formatted = meal_info.replace('<br/>', '\n')

            # 날짜 및 요일 업데이트
            meal_datetime = previous_date
            weekday_str = weekday_kor[meal_datetime.weekday()]

            # 임베드 업데이트
            embed.set_field_at(0, name='메뉴 목록', value=f"```\n{meal_info_formatted}\n```", inline=False)
            embed.title = f"{학교명}"
            embed.description = f'날짜 : {meal_datetime.month}월 {meal_datetime.day}일 ({weekday_str})'
            embed.set_footer(text=f'칼로리 정보: {calorie_info}' if calorie_info != "칼로리 정보가 없습니다." else None)
            await interaction.message.edit(embed=embed)

        # 다음날 버튼 콜백
        async def next_day_callback(interaction: disnake.CommandInteraction):
            nonlocal meal_date  # meal_date를 nonlocal로 선언하여 외부 변수 사용
            if not await check_user(interaction):
                return

            await interaction.followup.defer(ephemeral=False)

            next_date = datetime.strptime(meal_date, '%Y%m%d') + timedelta(days=1)
            meal_info, meal_date = await get_meal_info_async(학교명, edu_office_code, next_date.strftime('%Y%m%d'))
            calorie_info, _ = await get_calorie_info_async(학교명, edu_office_code, next_date.strftime('%Y%m%d'))
            meal_info_formatted = meal_info.replace('<br/>', '\n')

            # 날짜 및 요일 업데이트
            meal_datetime = next_date
            weekday_str = weekday_kor[meal_datetime.weekday()]

            # 임베드 업데이트
            embed.set_field_at(0, name='메뉴 목록', value=f"```\n{meal_info_formatted}\n```", inline=False)
            embed.title = f"{학교명}"
            embed.description = f'날짜 : {meal_datetime.month}월 {meal_datetime.day}일 ({weekday_str})'
            embed.set_footer(text=f'칼로리 정보: {calorie_info}' if calorie_info != "칼로리 정보가 없습니다." else None)
            await interaction.message.edit(embed=embed)

        # 버튼 콜백 설정
        이전날.callback = previous_day_callback
        다음날.callback = next_day_callback  # 다음날 버튼의 콜백 설정

        # 버튼 뷰 설정
        view = disnake.ui.View()
        view.add_item(이전날)
        view.add_item(세부사항)
        view.add_item(다음날)

        # 메시지 전송
        await ctx.send(embed=embed, view=view)

    except Exception as e:
        await ctx.send(f"Error: {str(e)}", ephemeral=True)

@bot.slash_command(name="날씨", description="날씨를 볼 수 있습니다.")
async def weather(ctx, region: str = commands.Param(name="지역", description="지역을 입력하세요.")):
    if not await check_permissions(ctx):
        return
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "날씨")
    await ctx.followup.defer(ephemeral=False)
    try:
        now = datetime.now()  # 현재 시각 가져오기

        검색 = region + " 날씨"
        url = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=" + 검색
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get(url, headers=hdr)
        html = req.text
        bsObj = bs4.BeautifulSoup(html, "html.parser")

        온도 = bsObj.find('div', class_='temperature_text')
        온도텍 = 온도.text
        온도결과 = re.sub(r'[^0-9.]', '', 온도텍.strip().split('°')[0])

        체감온도 = bsObj.find('div', class_='sort')
        체감온도텍 = 체감온도.text
        체감온도결과 = re.sub(r'[^0-9.]', '', 체감온도텍.strip().split('°')[0])

        미세먼지 = bsObj.find('li', class_='item_today level2')
        미세2 = 미세먼지.find('span', class_='txt')
        미세먼지결과 = 미세2.text
        
        if 미세먼지결과 == "좋음":
            미세결과 = "😀(좋음)"
        elif 미세먼지결과 == "보통":
            미세결과 = "😐(보통)"
        elif 미세먼지결과 == "나쁨":
            미세결과 = "😷(나쁨)"
        elif 미세먼지결과 == "매우나쁨":
            미세결과 = "😡(매우나쁨)"
        else:
            미세결과 = "정보 없음"

        초미세먼지들 = bsObj.find_all('li', class_='item_today level2')
        if len(초미세먼지들) >= 2:
            초미세먼지 = 초미세먼지들[1]  
            미세2 = 초미세먼지.find('span', class_='txt')
            초미세먼지결과 = 미세2.text
            if 초미세먼지결과 == "좋음":
                초미세결과 = "😀(좋음)"
            elif 초미세먼지결과 == "보통":
                초미세결과 = "😐(보통)"
            elif 초미세먼지결과 == "나쁨":
                초미세결과 = "😷(나쁨)"
            elif 초미세먼지결과 == "매우나쁨":
                초미세결과 = "😡(매우나쁨)"
            else:
                초미세결과 = "정보 없음"
        else:
            초미세결과 = "정보 없음"

        기후 = bsObj.find('p', class_='summary')
        기후2 = 기후.find('span', class_='weather before_slash')
        기후결과 = 기후2.text

        embed = disnake.Embed(title=region + ' 날씨 정보', description='현재 온도', color=disnake.Color(0x2ECCFA))
        embed.add_field(name=f"{온도결과}℃", value=f'체감 {체감온도결과}', inline=False)
        embed.add_field(name="미세먼지", value=f"{미세결과}", inline=False)
        embed.add_field(name="초미세먼지", value=f"{초미세결과}", inline=False)
        embed.add_field(name="기후", value=f"{기후결과}", inline=False)

        embed.set_footer(text=f"시각 : {now.hour}시 {now.minute}분 {now.second}초")
    
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send("올바른 지역을 입력해주세요")

@bot.slash_command(name="ai질문", description="GPT에게 질문하거나 DALL·E에게 이미지생성을 요청합니다. [회원전용]")
async def ai_ask(ctx: disnake.CommandInteraction, choice: str = commands.Param(name="모델", choices=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "DALL·E"]), ask: str = commands.Param(name="질문")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "ai질문")
    await membership(ctx)  # 회원 상태 확인

    if not ctx.response.is_done():
        await ctx.response.defer()  # 응답 지연

    # 사용자의 credit 확인
    user_credit = await get_user_credit(ctx.author.id)

    # DALL·E 사용 시 2크레딧, 다른 모델 사용 시 1크레딧
    credit_cost = 2 if choice == "DALL·E" else 1

    if user_credit < credit_cost:
        return await ctx.send("크레딧이 부족합니다. 더 이상 질문할 수 없습니다.")

    # credit 사용
    await use_user_credit(ctx.author.id, credit_cost)

    try:
        if choice == "DALL·E":
            # DALL·E 호출
            image_url = generate_image(ask)
            if "오류" in image_url:
                await ctx.followup.send(image_url)  # 후속 응답으로 보내기
            else:
                embed = disnake.Embed(title="이미지 생성", color=0x00ff00)
                embed.add_field(name="질문", value=f"{ask}", inline=False)
                embed.set_image(url=image_url)
                embed.add_field(name="이미지 링크", value=f"[전체 크기 보기]({image_url})", inline=False)
                await ctx.followup.send(embed=embed)  # 후속 응답으로 보내기
        else:
            # GPT API 호출
            answer = get_gpt_response(ask, choice)

            if len(answer) > 1024:
                # 답변이 1024자를 초과할 경우 텍스트 파일로 저장
                file_path = os.path.join(os.getcwd(), "답변.txt")  # 현재 작업 디렉토리 경로
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(answer)
                await ctx.followup.send("답변이 너무 길어 텍스트 파일로 전송합니다.", file=disnake.File(file_path))
                os.remove(file_path)  # 파일 전송 후 삭제
            else:
                # 임베드 응답 생성
                embed = disnake.Embed(title="GPT 응답", color=0x00ff00)
                embed.add_field(name="모델", value=f"{choice}", inline=False)
                embed.add_field(name="질문", value=f"{ask}", inline=False)
                embed.add_field(name="답변", value=f"{answer}", inline=False)
                await ctx.followup.send(embed=embed)  # 후속 응답으로 보내기

    except Exception as e:
        await ctx.followup.send(f"오류가 발생했습니다: {e}")

LANGUAGES = {
    'af': '아프리칸스 (afrikaans)',
    'sq': '알바니아어 (albanian)',
    'am': '암하라어 (amharic)',
    'ar': '아랍어 (arabic)',
    'hy': '아르메니아어 (armenian)',
    'az': '아제르바이잔어 (azerbaijani)',
    'eu': '바스크어 (basque)',
    'be': '벨라루스어 (belarusian)',
    'bn': '벵골어 (bengali)',
    'bs': '보스니아어 (bosnian)',
    'bg': '불가리아어 (bulgarian)',
    'ca': '카탈루냐어 (catalan)',
    'ceb': '세부아노어 (cebuano)',
    'ny': '치체와어 (chichewa)',
    'zh-cn': '중국어 (간체) (chinese (simplified))',
    'zh-tw': '중국어 (번체) (chinese (traditional))',
    'co': '코르시카어 (corsican)',
    'hr': '크로아티아어 (croatian)',
    'cs': '체코어 (czech)',
    'da': '덴마크어 (danish)',
    'nl': '네덜란드어 (dutch)',
    'en': '영어 (english)',
    'eo': '에스페란토 (esperanto)',
    'et': '에스토니아어 (estonian)',
    'tl': '필리핀어 (filipino)',
    'fi': '핀란드어 (finnish)',
    'fr': '프랑스어 (french)',
    'fy': '프리슬란드어 (frisian)',
    'gl': '갈리시아어 (galician)',
    'ka': '조지아어 (georgian)',
    'de': '독일어 (german)',
    'el': '그리스어 (greek)',
    'gu': '구자라트어 (gujarati)',
    'ht': '아이티 크리올어 (haitian creole)',
    'ha': '하우사어 (hausa)',
    'haw': '하와이어 (hawaiian)',
    'iw': '히브리어 (hebrew)',
    'he': '히브리어 (hebrew)',
    'hi': '힌디어 (hindi)',
    'hmn': '몽골어 (hmong)',
    'hu': '헝가리어 (hungarian)',
    'is': '아이슬란드어 (icelandic)',
    'ig': '이그보어 (igbo)',
    'id': '인도네시아어 (indonesian)',
    'ga': '아일랜드어 (irish)',
    'it': '이탈리아어 (italian)',
    'ja': '일본어 (japanese)',
    'jw': '자바어 (javanese)',
    'kn': '칸나다어 (kannada)',
    'kk': '카자흐어 (kazakh)',
    'km': '크메르어 (khmer)',
    'ko': '한국어 (korean)',
    'ku': '쿠르드어 (kurmanji)',
    'ky': '키르기스어 (kyrgyz)',
    'lo': '라오어 (lao)',
    'la': '라틴어 (latin)',
    'lv': '라트비아어 (latvian)',
    'lt': '리투아니아어 (lithuanian)',
    'lb': '룩셈부르크어 (luxembourgish)',
    'mk': '마케도니아어 (macedonian)',
    'mg': '말라가시어 (malagasy)',
    'ms': '말레이어 (malay)',
    'ml': '말라얄람어 (malayalam)',
    'mt': '몰타어 (maltese)',
    'mi': '마오리어 (maori)',
    'mr': '마라티어 (marathi)',
    'mn': '몽골어 (mongolian)',
    'my': '미얀마어 (burmese)',
    'ne': '네팔어 (nepali)',
    'no': '노르웨이어 (norwegian)',
    'or': '오디아어 (odia)',
    'ps': '파슈토어 (pashto)',
    'fa': '페르시아어 (persian)',
    'pl': '폴란드어 (polish)',
    'pt': '포르투갈어 (portuguese)',
    'pa': '펀자브어 (punjabi)',
    'ro': '루마니아어 (romanian)',
    'ru': '러시아어 (russian)',
    'sm': '사모아어 (samoan)',
    'gd': '스코틀랜드 게일어 (scots gaelic)',
    'sr': '세르비아어 (serbian)',
    'st': '세소토어 (sesotho)',
    'sn': '쇼나어 (shona)',
    'sd': '신디어 (sindhi)',
    'si': '신할라어 (sinhala)',
    'sk': '슬로바키아어 (slovak)',
    'sl': '슬로베니아어 (slovenian)',
    'so': '소말리어 (somali)',
    'es': '스페인어 (spanish)',
    'su': '순다어 (sundanese)',
    'sw': '스와힐리어 (swahili)',
    'sv': '스웨덴어 (swedish)',
    'tg': '타지크어 (tajik)',
    'ta': '타밀어 (tamil)',
    'te': '텔루구어 (telugu)',
    'th': '태국어 (thai)',
    'tr': '터키어 (turkish)',
    'uk': '우크라이나어 (ukrainian)',
    'ur': '우르두어 (urdu)',
    'ug': '위구르어 (uyghur)',
    'uz': '우즈벡어 (uzbek)',
    'vi': '베트남어 (vietnamese)',
    'cy': '웨일스어 (welsh)',
    'xh': '코사어 (xhosa)',
    'yi': '이디시어 (yiddish)',
    'yo': '요루바어 (yoruba)',
    'zu': '줄루어 (zulu)'
}

# LANGUAGES 딕셔너리를 언어 코드 목록으로 변환
LANGUAGE_CHOICES = list(LANGUAGES.keys())

@bot.slash_command(name="번역", description="텍스트를 선택한 언어로 번역합니다.")
async def translation(ctx, languages: str = commands.Param(name="언어"), text: str = commands.Param(name="내용")):
    if not await check_permissions(ctx):
        return
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "번역")
    translator = Translator()
    
    # 유효한 언어 코드인지 확인
    if languages not in LANGUAGE_CHOICES:
        embed = disnake.Embed(color=0xFF0000)
        embed.add_field(name="❌ 오류", value="유효한 언어 코드를 입력하세요.")
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    result = translator.translate(text, dest=languages)
    translated_text = result.text

    embed = disnake.Embed(title="번역 결과", color=0x00ff00)
    embed.add_field(name="언어", value=f"{LANGUAGES[languages]}")  # 선택한 언어 이름을 표시
    embed.add_field(name="원본 텍스트", value=text, inline=False)
    embed.add_field(name="번역된 텍스트", value=translated_text, inline=False)
    await ctx.send(embed=embed)

class LanguageView(disnake.ui.View):
    def __init__(self, languages, per_page=5):
        super().__init__(timeout=None)
        self.languages = languages
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(languages) - 1) // per_page
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):
        embed = disnake.Embed(title="지원 언어 목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page

        for lang_code, lang_name in list(self.languages.items())[start:end]:
            embed.add_field(name=lang_code, value=lang_name, inline=False)

        embed.add_field(name="", value=f"📄 페이지 {self.current_page + 1}/{self.max_page + 1}", inline=False)
        return embed


class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: LanguageView = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_message(interaction)


class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: LanguageView = self.view
        if view.current_page < view.max_page:
            view.current_page += 1
            await view.update_message(interaction)


@bot.slash_command(name="언어목록", description="지원하는 언어 목록을 확인합니다.")
async def language_list(ctx: disnake.CommandInteraction):
    view = LanguageView(LANGUAGES)
    view.message = await ctx.send(embed=await view.create_embed(), view=view)

@bot.slash_command(name="tts", description="입력한 텍스트를 음성으로 변환하여 재생합니다.")
async def tts(ctx: disnake.CommandInteraction, text: str = commands.Param(name="텍스트")):
    await ctx.response.defer()  # 응답 지연

    # 음성 채널에 연결
    voice_channel = ctx.author.voice.channel if ctx.author.voice else None
    if voice_channel is None:
        return await ctx.send("음성 채널에 들어가야 합니다.", ephemeral=True)

    # 현재 연결된 음성 클라이언트가 있는지 확인
    voice_client = disnake.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None:
        voice_client = await voice_channel.connect()
    else:
        # 이미 연결되어 있다면 기존 음성 클라이언트 사용
        await voice_client.move_to(voice_channel)

    # TTS 변환
    tts = gTTS(text=text, lang='ko')  # 한국어로 변환
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        tts.save(f"{tmp_file.name}.mp3")  # 임시 파일로 저장

        # 음성 파일 재생
        voice_client.play(disnake.FFmpegPCMAudio(f"{tmp_file.name}.mp3"))

        embed = disnake.Embed(title="TTS 재생", description=f"입력한 텍스트가 음성으로 변환되어 재생 중입니다:\n\n**{text}**", color=0x00ff00)
        await ctx.send(embed=embed, ephemeral=True)

        # 재생이 끝날 때까지 대기
        while voice_client.is_playing():
            await asyncio.sleep(1)  # asyncio.sleep 사용

# 유튜브 다운로드 설정
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# 음악 소스 클래스
class YTDLSource(disnake.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
    }

    def __init__(self, source, *, data):
        super().__init__(source)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        ydl = youtube_dl.YoutubeDL(cls.YTDL_OPTIONS)
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ydl.prepare_filename(data)
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# 음성 채널 별 대기열 및 클라이언트 관리
waiting_songs = defaultdict(list)
voice_clients = {}
current_song_index = defaultdict(int)

@bot.slash_command(name='재생', description='유튜브 링크 또는 제목으로 음악을 재생합니다.')
async def play(ctx, url_or_name: str):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return await ctx.send("권한이 없습니다.")

    await command_use_log(ctx, "재생")

    if ctx.author.voice is None:
        return await ctx.send("음성 채널에 연결되어 있지 않습니다. 먼저 음성 채널에 들어가세요.")

    channel_id = ctx.author.voice.channel.id

    # 음성 클라이언트 연결
    voice_client = await connect_voice_client(ctx, channel_id)

    # 현재 음악이 재생 중인 경우
    if voice_client.is_playing():
        return await ctx.send("현재 음악이 재생 중입니다. 새로운 노래를 추가할 수 없습니다.")

    # 플레이리스트 처리
    if await is_playlist(url_or_name):
        await handle_playlist(ctx, url_or_name, channel_id)
    else:
        await play_song(ctx, channel_id, url_or_name)

async def connect_voice_client(ctx, channel_id):
    if channel_id not in voice_clients or not voice_clients[channel_id].is_connected():
        voice_client = await ctx.author.voice.channel.connect()
        voice_clients[channel_id] = voice_client
    else:
        voice_client = voice_clients[channel_id]
    return voice_client

async def handle_playlist(ctx, url_or_name, channel_id):
    playlist_owner = await get_playlist_owner(url_or_name)

    if playlist_owner != ctx.author.id:
        embed = disnake.Embed(color=0xff0000, title="오류", description="이 플레이리스트의 소유자가 아닙니다.")
        return await ctx.send(embed=embed)

    songs = await get_songs_from_playlist(url_or_name)
    waiting_songs[channel_id].extend(songs)
    await play_next_song(ctx, channel_id)

async def play_song(ctx, channel_id, url_or_name):
    guild_id = ctx.guild.id
    voice_client = voice_clients.get(channel_id)

    if voice_client is None or not voice_client.is_connected():
        await ctx.send("음성 채널에 연결되어 있지 않습니다.")
        return

    if voice_client.is_playing():
        waiting_songs[channel_id].append(url_or_name)
        await ctx.send(f"현재 음악이 재생 중입니다. '{url_or_name}'가 끝나면 재생됩니다.")
        return

    try:
        player = await YTDLSource.from_url(f"ytsearch:{url_or_name}", loop=bot.loop, stream=True)
        embed = disnake.Embed(color=0x00ff00, title="음악 재생", description=f'재생 중: {player.title}\n[링크]({player.url})')
    except Exception as e:
        embed = disnake.Embed(color=0xff0000, title="오류", description=str(e))
        return await ctx.send(embed=embed)

    voice_client.play(player, after=lambda e: bot.loop.create_task(play_next_song(ctx, channel_id)))
    await send_control_buttons(ctx, embed)

async def play_next_song(ctx, channel_id):
    if ctx.guild.voice_client is None:
        await ctx.send("음성 클라이언트가 연결되어 있지 않습니다.")
        return

    if waiting_songs[channel_id]:
        next_song = waiting_songs[channel_id].pop(0)  # 대기열에서 다음 곡을 가져옴
        await play_song(ctx, channel_id, next_song)  # 다음 곡 재생
    else:
        await ctx.send("대기열이 비어 있습니다.")

@asynccontextmanager
async def connect_db():
    db_path = os.path.join('system_database', 'music.db')
    conn = await aiosqlite.connect(db_path)
    try:
        yield conn
    finally:
        await conn.close()

async def is_playlist(name):
    try:
        async with connect_db() as conn:
            cursor = await conn.execute("SELECT COUNT(DISTINCT playlist_name) FROM playlists WHERE playlist_name = ?", (name,))
            result = await cursor.fetchone()
            return result[0] > 0
    except aiosqlite.OperationalError as e:
        print(f"데이터베이스 오류: {e}")
        return False  # 또는 적절한 처리를 추가

async def get_playlist_owner(playlist_name):
    async with connect_db() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT user_id FROM playlists WHERE playlist_name = ?", (playlist_name,))
            owner = await cursor.fetchone()
    return owner[0] if owner else None

async def get_songs_from_playlist(playlist_name):
    async with connect_db() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT song FROM playlists WHERE playlist_name = ?", (playlist_name,))
            return [row[0] for row in await cursor.fetchall()]

async def send_control_buttons(ctx, embed):
    buttons = [
        disnake.ui.Button(label="일시 정지", style=disnake.ButtonStyle.red, custom_id="pause"),
        disnake.ui.Button(label="다시 재생", style=disnake.ButtonStyle.green, custom_id="resume"),
        disnake.ui.Button(label="음량 증가", style=disnake.ButtonStyle.blurple, custom_id="volume_up"),
        disnake.ui.Button(label="음량 감소", style=disnake.ButtonStyle.blurple, custom_id="volume_down"),
        disnake.ui.Button(label="노래 변경", style=disnake.ButtonStyle.grey, custom_id="change_song"),
    ]

    button_row = disnake.ui.View(timeout=None)
    for button in buttons:
        button_row.add_item(button)

    await ctx.send(embed=embed, view=button_row)

    # 각 버튼의 콜백 설정
    button_row.children[0].callback = lambda i: pause_callback(i, ctx)
    button_row.children[1].callback = lambda i: resume_callback(i, ctx)
    button_row.children[2].callback = lambda i: volume_change_callback(i, ctx, 0.1)
    button_row.children[3].callback = lambda i: volume_change_callback(i, ctx, -0.1)
    button_row.children[4].callback = lambda i: change_song_callback(i, ctx)

async def pause_callback(interaction, ctx):
    ctx.guild.voice_client.pause()
    await interaction.followup.send("음악이 정지되었습니다.", ephemeral=True)

async def resume_callback(interaction, ctx):
    if ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        await interaction.followup.send("음악을 재개했습니다.", ephemeral=True)
    else:
        await interaction.followup.send("현재 재생 중인 음악이 없습니다.", ephemeral=True)

async def volume_change_callback(interaction, ctx, change):
    if ctx.guild.voice_client.source:
        new_volume = min(max(ctx.guild.voice_client.source.volume + change, 0.0), 1.0)
        ctx.guild.voice_client.source.volume = new_volume
        await interaction.followup.send_message(f"현재 음량: {new_volume:.1f}", ephemeral=True)

async def change_song_callback(interaction, ctx):
    await interaction.followup.send_message("변경할 음악의 유튜브 링크 또는 음악 제목을 입력해주세요:", ephemeral=True)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        new_url_or_name = msg.content

        new_player = await YTDLSource.from_url(new_url_or_name, loop=bot.loop, stream=True)

        ctx.guild.voice_client.stop()
        ctx.guild.voice_client.play(new_player)

        change_embed = disnake.Embed(color=0x00ff00, description=f"새로운 음악을 재생합니다: {new_url_or_name}")
        await interaction.followup.send(embed=change_embed, ephemeral=True)

    except asyncio.TimeoutError:
        await interaction.followup.send("시간이 초과되었습니다. 다시 시도해주세요.", ephemeral=True)

@bot.slash_command(name='입장', description="음성 채널에 입장합니다.")
async def join(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "입장")
    embed = disnake.Embed(color=0x00ff00)
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.move_to(channel)
            embed.description = "음성 채널로 이동했습니다."
        else:
            await channel.connect()
            embed.description = "음성 채널에 연결되었습니다."
    else:
        embed.description = "음성 채널에 연결되어 있지 않습니다."
        embed.color = 0xff0000

    await ctx.send(embed=embed)

@bot.slash_command(name='볼륨', description="플레이어의 볼륨을 변경합니다.")
async def volume(ctx, volume: int):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "볼륨")
    embed = disnake.Embed(color=0x00ff00)
    if ctx.guild.voice_client is None:
        embed.description = "음성 채널에 연결되어 있지 않습니다."
        embed.color = 0xff0000
    else:
        ctx.guild.voice_client.source.volume = volume / 100
        embed.description = f"볼륨을 {volume}%로 변경했습니다."

    await ctx.send(embed=embed)

@bot.slash_command(name='정지', description="음악을 중지하고 음성 채널에서 나갑니다.")
async def stop(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "정지")
    await ctx.response.defer()
    embed = disnake.Embed(color=0x00ff00)
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        embed.description = "음악을 중지하고 음성 채널에서 나갔습니다."
    else:
        embed.description = "봇이 음성 채널에 연결되어 있지 않습니다."
        embed.color = 0xff0000

    await ctx.send(embed=embed)

@bot.slash_command(name='일시정지', description="음악을 일시정지합니다.")
async def pause(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "일시정지")
    embed = disnake.Embed(color=0x00ff00)
    if ctx.guild.voice_client is None or not ctx.guild.voice_client.is_playing():
        embed.description = "음악이 이미 일시 정지 중이거나 재생 중이지 않습니다."
        embed.color = 0xff0000
    else:
        ctx.guild.voice_client.pause()
        embed.description = "음악을 일시 정지했습니다."

    await ctx.send(embed=embed)

@bot.slash_command(name='다시재생', description="일시중지된 음악을 다시 재생합니다.")
async def resume(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "다시재생")
    voice_client = ctx.guild.voice_client

    if voice_client is None:
        await ctx.send("봇이 음성 채널에 연결되어 있지 않습니다.")
        return

    embed = disnake.Embed(color=0x00ff00)
    if voice_client.is_playing() or not voice_client.is_paused():
        embed.description = "음악이 이미 재생 중이거나 재생할 음악이 존재하지 않습니다."
        embed.color = 0xff0000
    else:
        voice_client.resume()
        embed.description = "음악을 재개했습니다."

    await ctx.send(embed=embed)

# 플레이리스트 생성 제한 설정
MAX_PLAYLISTS = {
    0 : 5,
    1 : 20,
    2 : 30,
    3 : 50,
    4 : 80,
    5 : 100
}

@bot.slash_command(name='플레이리스트', description='플레이리스트를 확인합니다.')
async def view_playlist(ctx, playlist_name: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "플레이리스트")
    db_path = os.path.join('system_database', 'music.db')
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute('SELECT song FROM playlists WHERE user_id = ? AND playlist_name = ?',
                                     (ctx.author.id, playlist_name))
        songs = await cursor.fetchall()
        
        embed = disnake.Embed(title=f"{playlist_name} 플레이리스트", color=0x00FF00)  # 초록색 임베드

        if songs:
            song_list = "\n".join([song[0] for song in songs])
            embed.add_field(name="곡 목록", value=song_list, inline=False)
        else:
            embed.add_field(name="정보", value=f"{playlist_name} 플레이리스트가 비어 있습니다.", inline=False)

        await ctx.send(embed=embed)

@bot.slash_command(name='플레이리스트_추가', description='플레이리스트에 음악을 추가합니다.')
async def add_to_playlist(ctx, playlist_name: str, song: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "플레이리스트_추가")
    db_path = os.path.join('system_database', 'music.db')
    async with aiosqlite.connect(db_path) as economy_aiodb:
        db_path = os.path.join('system_database', 'membership.db')
        async with aiosqlite.connect(db_path) as membership_db:
            # 사용자 클래스 확인
            async with membership_db.execute('SELECT class FROM user WHERE id = ?', (ctx.author.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    user_class = row[0]
                else:
                    await ctx.send("사용자 정보를 찾을 수 없습니다.")
                    return

            # 최대 플레이리스트 수 확인
            async with economy_aiodb.execute('SELECT COUNT(*) FROM playlists WHERE user_id = ?', (ctx.author.id,)) as cursor:
                count = await cursor.fetchone()
                current_count = count[0]

            if current_count >= MAX_PLAYLISTS.get(user_class, 0):
                embed = disnake.Embed(color=0xFF0000)
                if user_class == 0:
                    user_class_text = "비회원"
                elif user_class == 1:
                    user_class_text = "브론즈_회원"
                elif user_class == 2:
                    user_class_text = "실버_회원"
                elif user_class == 3:
                    user_class_text = "다이아_회원"
                elif user_class == 4:
                    user_class_text = "레전드_회원"
                elif user_class == 5:
                    user_class_text = "개발자"
                else:
                    print("플레이리스트 오류")
                    return
                max_playlists = MAX_PLAYLISTS.get(user_class)
                embed.add_field(name="오류", value=f"{user_class_text}는 최대 {max_playlists}개의 플레이리스트를 생성할 수 있습니다.", inline=False)
                await ctx.send(embed=embed)
                return

            # 음악 추가
            try:
                async with economy_aiodb.execute('INSERT INTO playlists (user_id, playlist_name, song) VALUES (?, ?, ?)',
                                                  (ctx.author.id, playlist_name, song)):
                    await economy_aiodb.commit()
                embed = disnake.Embed(title="추가 완료", color=0x00FF00)
                embed.add_field(name="플레이리스트", value=f"{playlist_name} 플레이리스트에 {song}이(가) 추가되었습니다.", inline=False)
                await ctx.send(embed=embed)
            except aiosqlite.IntegrityError:
                embed = disnake.Embed(title="오류", color=0xFF0000)
                embed.add_field(name="오류", value=f"{playlist_name} 플레이리스트에 이미 {song}이(가) 존재합니다.", inline=False)
                await ctx.send(embed=embed)

@bot.slash_command(name='플레이리스트_삭제', description='플레이리스트에서 음악을 삭제합니다.')
async def remove_from_playlist(ctx, playlist_name: str, song: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "플레이리스트_삭제")
    db_path = os.path.join('system_database', 'music.db')
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute('DELETE FROM playlists WHERE user_id = ? AND playlist_name = ? AND song = ?',
                                     (ctx.author.id, playlist_name, song))
        await conn.commit()
        
        embed = disnake.Embed(title="삭제 결과", color=0x00FF00)

        if cursor.rowcount > 0:
            embed.add_field(name="성공", value=f"{playlist_name} 플레이리스트에서 {song}이(가) 삭제되었습니다.", inline=False)
        else:
            embed.add_field(name="정보", value=f"{playlist_name} 플레이리스트에 {song}이(가) 없습니다.", inline=False)

        await ctx.send(embed=embed)

@bot.slash_command(name='인증_문자', description='문자를 이용해서 인증을 합니다.')
async def sms_verify(ctx, phone_number: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "인증_문자")
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
    
    if not os.path.exists(db_path):
        await database_create(ctx)
    else:
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT 인증역할, 인증채널 FROM 설정")
        role_id, channel_id = await aiocursor.fetchone()
        await aiocursor.close()
        await aiodb.close()

    if role_id:
        role = ctx.guild.get_role(role_id)
        if role:
            # 인증 역할이 이미 부여된 경우
            if role in ctx.author.roles:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이미 인증된 상태입니다.")
                await ctx.send(embed=embed, ephemeral=True)
                return
            if channel_id:
                channel = ctx.guild.get_channel(channel_id)
                if channel and channel == ctx.channel:
                    # 인증 채널에서만 작동하는 코드 작성
                    verify_code = random.randint(100000, 999999)
                    text = f"인증번호: {verify_code}"
                    
                    # 카카오 알림톡 메시지 전송
                    message = {
                        'messages': [{
                            'to': phone_number,
                            'from': sec.send_number,
                            'text': text,
                            'kakaoOptions': {
                                'pfId': sec.kakao_pfid,
                                'templateId': sec.kakao_templateid,
                                'variables': {
                                    '#{verify_code}': verify_code,
                                    '#{activity}': "스톤봇 인증"
                                }
                            }
                        }]
                    }
                    if coolsms_kakao.send_kakao(message):  # 카카오 알림톡 전송
                        embed = disnake.Embed(color=embedsuccess)
                        embed.add_field(name="문자 인증", value=f"**{phone_number}** 으로 인증번호를 전송했습니다.")
                        await ctx.send(embed=embed, ephemeral=True)
                        print(f'''인증번호({verify_code})가 "{phone_number}"로 전송되었습니다.''')

                        def check(m):
                            return m.author == ctx.author and m.content == str(verify_code)

                        try:
                            msg = await bot.wait_for('message', check=check, timeout=180)
                            if msg:
                                await ctx.channel.purge(limit=1)
                                await ctx.author.add_roles(role)
                                embed = disnake.Embed(color=embedsuccess)
                                embed.add_field(name="문자 인증", value=f"{ctx.author.mention} 문자 인증이 완료되었습니다.")
                                await ctx.send(embed=embed)
                        except disnake.TimeoutError:
                            embed = disnake.Embed(color=embederrorcolor)
                            embed.add_field(name="❌ 오류", value="인증 시간이 초과되었습니다. 다시 시도해주세요.")
                            await ctx.send(embed=embed)
                    else:
                        embed = disnake.Embed(color=embederrorcolor)
                        embed.add_field(name="❌ 오류", value="카카오 알림톡 전송에 실패했습니다.")
                        await ctx.send(embed=embed, ephemeral=True)
                else:
                    embed = disnake.Embed(color=embederrorcolor)
                    embed.add_field(name="❌ 오류", value="인증 채널에서만 인증 명령어를 사용할 수 있습니다.")
                    await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="인증채널이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
            await ctx.send(embed=embed, ephemeral=True)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
        await ctx.send(embed=embed, ephemeral=True)
        
@bot.slash_command(name='인증_이메일', description='이메일을 이용해서 인증을 합니다.')
async def email_verify(ctx, email: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "인증_이메일")
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")

    # 데이터베이스가 존재하지 않는 경우
    if not os.path.exists(db_path):
        await database_create(ctx)
        await ctx.send("데이터베이스가 생성되었습니다.", ephemeral=True)
        return

    # 데이터베이스 연결 및 설정 가져오기
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.execute("SELECT 인증역할, 인증채널 FROM 설정")
    row = await aiocursor.fetchone()
    await aiocursor.close()
    await aiodb.close()

    role_id, channel_id = row if row else (None, None)

    if role_id:
        role = ctx.guild.get_role(role_id)

        if role:
            # 인증 역할이 이미 부여된 경우
            if role in ctx.author.roles:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이미 인증된 상태입니다.")
                await ctx.send(embed=embed, ephemeral=True)
                return

            if channel_id:
                channel = ctx.guild.get_channel(channel_id)
                if channel and channel == ctx.channel:
                    # 인증 코드 생성 및 이메일 전송
                    verifycode = random.randint(100000, 999999)
                    send_email(ctx, email, verifycode)
                    embed = disnake.Embed(color=0x00FF00)
                    embed.add_field(name="이메일 인증", value=f"**{email}** 으로 인증번호를 전송했습니다.")
                    await ctx.send(embed=embed, ephemeral=True)
                    print(f'''인증번호({verifycode})가 "{email}"로 전송되었습니다.''')

                    def check(m):
                        return m.author == ctx.author and m.content == str(verifycode)

                    try:
                        msg = await bot.wait_for('message', check=check, timeout=180)
                        await ctx.channel.purge(limit=1)
                        await ctx.author.add_roles(role)
                        embed = disnake.Embed(color=0x00FF00)
                        embed.add_field(name="이메일 인증", value=f"{ctx.author.mention} 메일 인증이 완료되었습니다.")
                        await ctx.send(embed=embed)
                    except disnake.TimeoutError:
                        embed = disnake.Embed(color=embederrorcolor)
                        embed.add_field(name="❌ 오류", value="인증 시간이 초과되었습니다. 다시 시도해주세요.")
                        await ctx.send(embed=embed)
                else:
                    embed = disnake.Embed(color=embederrorcolor)
                    embed.add_field(name="❌ 오류", value="인증 채널에서만 인증 명령어를 사용할 수 있습니다.")
                    await ctx.send(embed=embed, ephemeral=True)
            else:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="인증채널이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
                await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
            await ctx.send(embed=embed, ephemeral=True)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="인증", description="캡챠를 이용해서 인증을 합니다.")
async def captcha_verify(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "인증")
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
    if not os.path.exists(db_path):
        await database_create(ctx)
    else:
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT 인증역할, 인증채널 FROM 설정")
        role_id, channel_id = await aiocursor.fetchone()
        await aiocursor.close()
        await aiodb.close()
    if role_id:
        role_id = role_id
        role = ctx.guild.get_role(role_id)
        if role:
            # 인증 역할이 이미 부여된 경우
            if role in ctx.author.roles:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이미 인증된 상태입니다.")
                await ctx.send(embed=embed, ephemeral=True)
                return
            if channel_id:
                channel_id = channel_id
                channel = ctx.guild.get_channel(channel_id)
                if channel and channel == ctx.channel:
                    # 인증 채널에서만 작동하는 코드 작성
                    image_captcha = ImageCaptcha()
                    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    data = image_captcha.generate(captcha_text)
                    image_path = 'captcha.png'  # 이미지 파일 경로
                    with open(image_path, 'wb') as f:
                        f.write(data.getvalue())  # BytesIO 객체를 파일로 저장
                    embed = disnake.Embed(color=embedsuccess)
                    embed.add_field(name="인증", value="코드를 입력해주세요(6 자리)")
                    file = disnake.File(image_path, filename='captcha.png')
                    embed.set_image(url="attachment://captcha.png")  # 이미지를 임베드에 첨부
                    await ctx.send(embed=embed, file=file, ephemeral=True)
                    def check(m):
                        return m.author == ctx.author and m.content == captcha_text
                    try:
                        msg = await bot.wait_for('message', timeout=60.0, check=check)
                        await ctx.channel.purge(limit=1)
                    except TimeoutError:
                        await ctx.channel.purge(limit=1)
                        embed = disnake.Embed(color=embederrorcolor)
                        embed.add_field(name="❌ 오류", value="시간이 초과되었습니다. 다시 시도해주세요.")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.author.add_roles(role)
                        embed = disnake.Embed(color=embedsuccess)
                        embed.add_field(name="인증 완료", value=f"{ctx.author.mention} 캡챠 인증이 완료되었습니다.")
                        await ctx.send(embed=embed)
                else:
                    embed = disnake.Embed(color=embederrorcolor)
                    embed.add_field(name="❌ 오류", value="인증 채널에서만 인증 명령어를 사용할 수 있습니다.")
                    await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="인증채널을 선택해주세요.")
                await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="인증역할을 찾을 수 없습니다.")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="인증역할을 선택해주세요.")
        await ctx.send(embed=embed)

@bot.slash_command(name="지갑", description="자신이나 다른 유저의 지갑을 조회합니다.")
async def wallet(ctx, member_id: str = None):
    try:
        if not await check_permissions(ctx):
            return

        await command_use_log(ctx, "지갑")

        if not await member_status(ctx):
            return

        await ctx.response.defer()

        user = ctx.author if member_id is None else await bot.fetch_user(member_id)
        if user is None:
            await ctx.followup.send("유효하지 않은 유저 ID입니다.", ephemeral=True)
            return

        user_data = await fetch_user_data(user.id)
        if user_data is None:
            await ctx.followup.send(f"{user.mention}, 가입되지 않은 유저입니다.", ephemeral=True)
            return

        tos_data = await fetch_tos_status(user.id)
        tos = tos_data[0] if tos_data else None

        if tos is None:
            await ctx.followup.send(f"{user.mention}, TOS 정보가 없습니다.", ephemeral=True)
            return
        if tos == 1:
            await ctx.followup.send(f"{user.mention}, 이용제한된 유저입니다.", ephemeral=True)
            return

        money, level, exp, lose_money = user_data[1], user_data[3], user_data[4], user_data[5]
        
        embed = disnake.Embed(title=f"{user.name}님의 지갑 💰", color=0x00ff00)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="아이디", value=f"{user.id}", inline=False)
        embed.add_field(name="레벨", value=f"{level:,}({exp:,}) Level", inline=False)
        embed.add_field(name="잔액", value=f"{money:,}원", inline=False)
        embed.add_field(name="잃은돈", value=f"{lose_money:,}원", inline=False)

        await ctx.followup.send(embed=embed, ephemeral=True)

    except Exception as e:
        await ctx.followup.send("명령어 처리 중 오류가 발생했습니다.", ephemeral=True)

@bot.slash_command(name="돈순위", description="가장 돈이 많은 유저의 리스트를 보여줍니다.")
async def money_ranking(ctx: disnake.CommandInteraction):
    if not await check_permissions(ctx):
        return
    
    await command_use_log(ctx, "돈순위")
    limit = 10

    excluded_ids = developer if isinstance(developer, list) else [developer]
    richest_users = await fetch_money_ranking(excluded_ids, limit)

    if not richest_users:
        embed = disnake.Embed(color=embederrorcolor, description="등록된 유저가 없습니다.")
        await ctx.send(embed=embed, ephemeral=True)
    else:
        embed = disnake.Embed(title="돈순위", color=0x00ff00)
        for rank, (user_id, money) in enumerate(richest_users, start=1):
            embed.add_field(name=f"{rank}위: {user_id}", value=f"돈: {money}", inline=False)

        await ctx.send(embed=embed)

@bot.slash_command(name="돈관리", description="유저의 돈을 관리합니다. [개발자전용]")
async def money_edit(ctx, user: str = commands.Param(name="유저"), choice: str = commands.Param(name="선택", choices=["차감", "추가"]), money: int = commands.Param(name="돈")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "돈관리")
    
    if ctx.author.id == developer:
        # 멘션 또는 ID에서 사용자 ID 추출
        try:
            user_id = None
            
            # 멘션 형식 처리
            if user.startswith('<@') and user.endswith('>'):
                user_id = int(user[3:-1]) if user[2] == '!' else int(user[2:-1])  # <@!123456789> 또는 <@123456789>
            else:
                user_id = int(user)  # ID 형식

            user_obj = ctx.guild.get_member(user_id)
            if user_obj is None:
                raise ValueError("사용자를 찾을 수 없습니다.")
        except ValueError:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="유효한 사용자 멘션 또는 ID를 입력하세요.")
            await ctx.send(embed=embed, ephemeral=True)
            return

        # 돈 차감 또는 추가
        if choice == "차감":
            if not await removemoney(user_obj.id, money):
                return await ctx.send("그 사용자의 포인트를 마이너스로 줄 수 없어요!")
            embed = disnake.Embed(title="잔액 차감", color=embedsuccess)
            embed.add_field(name="차감 금액", value=f"{money:,}원")
            embed.add_field(name="대상", value=f"{user_obj.mention}")
            await ctx.send(embed=embed)
        elif choice == "추가":
            await addmoney(user_obj.id, money)
            embed = disnake.Embed(title="잔액 추가", color=embedsuccess)
            embed.add_field(name="추가 금액", value=f"{money:,}원")
            embed.add_field(name="대상", value=f"{user_obj.mention}")
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="차감 또는 추가 중 선택해주세요.")
            await ctx.send(embed=embed, ephemeral=True)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="일하기", description="간단한 문제풀이로 10,000 ~ 100,000원을 얻습니다.")
async def earn_money(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "일하기")
    if not await member_status(ctx):
        return
    cooldowns = load_cooldowns()
    last_execution_time = cooldowns.get(str(ctx.author.id), 0)
    current_time = time.time()
    cooldown_time = 600
    if current_time - last_execution_time < cooldown_time:
        remaining_time = round(cooldown_time - (current_time - last_execution_time))
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="쿨타임", value=f"{ctx.author.mention}, {remaining_time}초 후에 다시 시도해주세요.")
        await ctx.send(embed=embed)
        return
    number_1 = random.randrange(2, 10)
    number_2 = random.randrange(2, 10)
    random_add_money = random.randrange(10000, 100001)
    random_add_money = int(round(random_add_money, -3))

    correct_answer = number_1 + number_2
    await ctx.send(f"{number_1} + {number_2} =")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and int(msg.content) == correct_answer
    try:
        msg = await bot.wait_for('message', timeout=15.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('시간이 초과되었습니다. 다음 기회에 도전해주세요.')
    else:
        if msg.content == str(correct_answer):
            cooldowns[str(ctx.author.id)] = current_time
            save_cooldowns(cooldowns)
            embed = disnake.Embed(color=embedsuccess)
            await addmoney(ctx.author.id, random_add_money)
            await add_exp(ctx.author.id, round(random_add_money / 300))
            embed.add_field(name="정답", value=f"{ctx.author.mention}, {random_add_money:,}원이 지급되었습니다.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f'틀렸습니다! 정답은 {correct_answer}입니다.')

@bot.slash_command(name="출석체크", description="봇 투표 여부를 확인하고 돈을 지급합니다.")
async def check_in(ctx: disnake.CommandInteraction):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "출석체크")

    user_id = ctx.author.id
    
    # 상대 경로 설정 (현재 작업 디렉토리 기준)
    db_path = os.path.join('system_database', 'economy.db')

    async with aiosqlite.connect(db_path) as conn:
        async with conn.cursor() as cursor:
            # 사용자 출석 체크 상태 조회
            await cursor.execute("SELECT checkin FROM user WHERE id = ?", (user_id,))
            result = await cursor.fetchone()

            if result is None:
                # 사용자 정보가 없으면 신규 사용자로 추가
                await cursor.execute("INSERT INTO user (id, checkin) VALUES (?, ?)", (user_id, 0))
                await conn.commit()
                check_status = 0  # 신규 사용자이므로 check_status를 0으로 설정
            else:
                check_status = int(result[0])  # 튜플에서 값 추출

            if check_status == 0:
                # 출석 체크하지 않은 상태
                payment_amount = 200000  # 지급 금액
                await addmoney(user_id, payment_amount)

                # 출석 체크 상태 업데이트
                await cursor.execute("UPDATE user SET checkin = 1 WHERE id = ?", (user_id,))
                await conn.commit()

                embed = disnake.Embed(title="✅ 출석 체크 완료", color=0x00FF00)
                embed.add_field(name="금액 지급", value=f"{payment_amount:,}원이 지급되었습니다.")
                await ctx.send(embed=embed)
            else:
                embed = disnake.Embed(title="❌ 출석 체크 실패", color=0xFF0000)
                embed.add_field(name="오류", value="이미 출석 체크를 하였습니다.")
                await ctx.send(embed=embed)

@bot.slash_command(name="송금", description="돈 송금")
async def send_money(ctx, get_user: disnake.Member = commands.Param(name="받는사람"), money: int = commands.Param(name="금액")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "송금")
    if not await member_status(ctx):
        return
    db_path = os.path.join('system_database', 'economy.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (get_user.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata is not None:
        if int(dbdata[0]) == 1:
            embed=disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="받는사람이 이용제한상태이므로 송금할수없습니다.")
            await ctx.send(embed=embed, ephemeral=True)
            return
        else:
            pass
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="받는사람이 미가입상태이므로 송금할수없습니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    if money < 1:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="송금 금액은 1원이상부터 가능합니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    send_user = ctx.author
    send_user_money = await getmoney(send_user.id)
    if send_user_money < money:
        return await ctx.send(f"{send_user.mention}님의 잔액이 부족하여 송금할 수 없습니다.")
    await removemoney(send_user.id, money)
    await addmoney(get_user.id, money)
    embed = disnake.Embed(title="송금 완료", color=embedsuccess)
    embed.add_field(name="송금인", value=f"{send_user.mention}")
    embed.add_field(name="받는사람", value=f"{get_user.mention}")
    embed.add_field(name="송금 금액", value=f"{money:,}")
    await ctx.send(embed=embed)

@bot.slash_command(name="가위바위보", description="봇과 가위바위보 도박을 합니다. (확률 33.3%, 2배, 실패시 -1배)")
async def rock_paper_scissors_betting(ctx, user_choice: str = commands.Param(name="선택", choices=["가위", "바위", "보"]), bet_amount: int = commands.Param(name="금액")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "가위바위보")
    if not await member_status(ctx):
        return
    user = ctx.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회

    # 배팅 금액이 음수이거나 0일 경우 오류 메시지 전송
    if bet_amount <= 0:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="배팅 금액은 1원 이상이어야 합니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if bet_amount > current_money:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가지고 있는 돈보다 배팅 금액이 많습니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    bot_choice = random.choice(["가위", "바위", "보"])

    # 결과 판단
    result_embed = disnake.Embed(title="게임 결과", color=0x00FF00)  # 초록색 임베드
    result_embed.add_field(name="당신의 선택", value=user_choice, inline=True)
    result_embed.add_field(name="봇의 선택", value=bot_choice, inline=True)

    if user_choice == bot_choice:
        result = "비겼습니다!"
        result_embed.add_field(name="결과", value=result, inline=False)
        result_embed.add_field(name="돈은 그대로 유지됩니다.", value=f"현재 금액: {current_money:,}원", inline=False)
    elif (user_choice == "가위" and bot_choice == "보") or \
         (user_choice == "바위" and bot_choice == "가위") or \
         (user_choice == "보" and bot_choice == "바위"):
        result = "당신이 이겼습니다!"
        await addmoney(user.id, bet_amount)  # 돈을 추가
        await add_exp(user.id, round(bet_amount / 600))
        result_embed.add_field(name="결과", value=result, inline=False)
        result_embed.add_field(name="보상", value=f"{bet_amount * 2:,}원을 얻었습니다.", inline=False)
    else:
        result = "당신이 졌습니다!"
        await removemoney(user.id, bet_amount)  # 돈을 제거
        await add_lose_money(user.id, bet_amount)
        await add_exp(user.id, round(bet_amount / 1200))
        result_embed.add_field(name="결과", value=result, inline=False)
        result_embed.add_field(name="패배", value=f"{bet_amount:,}원을 잃었습니다.", inline=False)

    # 결과 메시지 전송
    await ctx.send(embed=result_embed)

betting_method_choices = ["도박 (확률 30%, 2배, 실패시 -1배)", "도박2 (확률 50%, 1.5배, 실패시 -0.75배)"]
@bot.slash_command(name="도박", description="보유금액으로 도박을 합니다.")
async def betting(ctx, money: int = commands.Param(name="금액"), betting_method: str = commands.Param(name="배팅종류", choices=betting_method_choices)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "도박")
    if not await member_status(ctx):
        return
    user = ctx.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회

    if money <= 0:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="배팅 금액은 1원 이상이어야 합니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    if money > current_money:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가지고 있는 돈보다 배팅 금액이 많습니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    if betting_method == "도박 (확률 30%, 2배, 실패시 -1배)":
        await handle_bet(ctx, user, money, success_rate=30, win_multiplier=2, lose_multiplier=1, lose_exp_divisor=1200)
    elif betting_method == "도박2 (확률 50%, 1.5배, 실패시 -0.75배)":
        await handle_bet(ctx, user, money, success_rate=50, win_multiplier=0.5, lose_multiplier=0.75, lose_exp_divisor=1200)

@bot.slash_command(name="숫자도박", description="보유금액으로 도박을 합니다. (숫자맞추기 1~4, 확률 25%, 최대 3배, 실패시 -2배)")
async def betting_number(ctx, number: int = commands.Param(name="숫자"), money: int = commands.Param(name="금액")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "숫자도박")
    if not await member_status(ctx):
        return
    user = ctx.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회

    # 배팅 금액이 음수이거나 0일 경우 오류 메시지 전송
    if money <= 0:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="배팅 금액은 1원 이상이어야 합니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    if round(money * 2) > current_money:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가진금액보다 배팅금이 많습니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return
    else:
        if number < 1 or number > 4:  # 1~4 범위 체크
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="1 ~ 4 중에서 선택해주세요.")
            await ctx.send(embed=embed, ephemeral=True)
            return

        random_number = random.randint(1, 5)  # 1~4 범위의 랜덤 숫자 생성
        if random_number == number:
            await addmoney(user.id, (money * 2))
            await add_exp(user.id, round((money * 2) / 600))
            embed = disnake.Embed(color=embedsuccess)
            money = money * 3
            embed.add_field(name="성공", value=f"{money:,}원을 얻었습니다.")
            await ctx.send(embed=embed)
        else:
            await removemoney(user.id, round(money * 2))
            await add_lose_money(user.id, round(money * 2))
            await add_exp(user.id, round((money * 2) / 1200))
            embed = disnake.Embed(color=embederrorcolor)
            money = round(money * 2)
            embed.add_field(name="실패", value=f"{money:,}원을 잃었습니다.")
            await ctx.send(embed=embed)

# 카드 점수 계산 함수
def get_card_value(card):
    shape_score = {
        'A': 1,
        'J': 0,
        'Q': 0,
        'K': 0,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10': 0
    }
    return shape_score.get(card, 0)

@bot.slash_command(name="도박_바카라", description="보유금액으로 도박을 합니다.")
async def betting_card(ctx, money: int = commands.Param(name="금액"), method: str = commands.Param(name="배팅", choices=["플레이어", "무승부", "뱅커"])):
    if not await check_permissions(ctx):
        return

    await ctx.response.defer()  # 응답을 지연시키기 위해 defer 호출

    await command_use_log(ctx, "도박_바카라")
    
    if not await member_status(ctx):
        return

    user = ctx.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회

    # 배팅 금액 검증
    if money <= 0:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="배팅 금액은 1원 이상이어야 합니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    if money > current_money:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가진 금액보다 배팅 금액이 많습니다.")
        await ctx.send(embed=embed, ephemeral=True)
        return

    # 카드 랜덤 생성 함수
    def random_card():
        return random.choice(['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'])

    def random_shape():
        return random.choice(['♠️', '♣️', '♥️', '♦️'])

    # 카드와 모양 랜덤 생성
    mix_p = [random_card() for _ in range(3)]
    mix_b = [random_card() for _ in range(3)]
    shape_p = [random_shape() for _ in range(3)]
    shape_b = [random_shape() for _ in range(3)]

    # 점수 계산
    score_calculate_p = (get_card_value(mix_p[0]) + get_card_value(mix_p[1])) % 10
    score_calculate_b = (get_card_value(mix_b[0]) + get_card_value(mix_b[1])) % 10

    # 플레이어 추가 카드 규칙 적용
    add_card_p = False
    if score_calculate_p <= 6:
        mix_p[2] = random_card()
        score_calculate_p = (get_card_value(mix_p[0]) + get_card_value(mix_p[1]) + get_card_value(mix_p[2])) % 10
        add_card_p = True

    # 뱅커의 추가 카드 규칙 적용
    add_card_b = False
    if score_calculate_b <= 2 or (
        score_calculate_b == 3 and score_calculate_p != 8) or (
        score_calculate_b == 4 and score_calculate_p in range(2, 8)) or (
        score_calculate_b == 5 and score_calculate_p in range(4, 8)) or (
        score_calculate_b == 6 and score_calculate_p in [6, 7]):
        mix_b[2] = random_card()
        score_calculate_b = (get_card_value(mix_b[0]) + get_card_value(mix_b[1]) + get_card_value(mix_b[2])) % 10
        add_card_b = True

    # 승자 결정
    winner = "플레이어" if score_calculate_p > score_calculate_b else "뱅커" if score_calculate_p < score_calculate_b else "무승부"

    # 승리 데이터 업데이트
    db_path = os.path.join('system_database', 'baccarat.db')
    async with aiosqlite.connect(db_path) as db:
        await db.execute('INSERT INTO winner (winner) VALUES (?)', (winner,))
        await db.commit()

    # 배팅 결과 처리
    embed = disnake.Embed(color=embedsuccess if winner == method else embederrorcolor)

    if winner == method:  # win
        win_money = money * (2 if winner == "플레이어" else 1.95)
        await addmoney(user.id, win_money - money)
        await add_exp(user.id, round((money * 2) / 600))
        embed.add_field(name="성공", value=f"{win_money:,}원을 얻었습니다.", inline=False)
    else:  # lose
        if winner == "무승부":
            embed.add_field(name="무승부", value="배팅 금액이 유지됩니다.", inline=False)
        else:
            await removemoney(user.id, money)
            await add_lose_money(user.id, money)
            await add_exp(user.id, round(money / 1200))
            embed.add_field(name="실패", value=f"{money:,}원을 잃었습니다.", inline=False)

    # 카드 결과 출력
    embed.add_field(name="결과", value=f"배팅 : {method}\n배팅금액 : {money:,}원\n승리 : {winner}!", inline=False)

    # 추가 카드 결과 표시
    card_results = f"플레이어 : {', '.join([f'{mix_p[i]}{shape_p[i]}' for i in range(3)])}, {score_calculate_p}\n"
    card_results += f"뱅커 : {', '.join([f'{mix_b[i]}{shape_b[i]}' for i in range(3)])}, {score_calculate_b}"
    embed.add_field(name="카드 결과", value=card_results)

    await ctx.send(embed=embed)

@bot.slash_command(name="로또구매", description="로또을 구매합니다.")
async def purchase_lottery(interaction: disnake.ApplicationCommandInteraction, auto: bool = False, count: int = 1, numbers: str = None):
    user_id = interaction.author.id

    # 최대 구매 개수 제한
    if count > 100:
        await interaction.send("최대 100개까지 로또을 구매할 수 있습니다.")
        return

    # 로또 음수제한
    if count < 1:
        await interaction.send("로또는 1개이상만 구매할수 있습니다.")
        return

    # 사용자의 잔액을 가져옵니다.
    get_money = await getmoney(user_id)
    
    total_cost = count * 10000  # 총 비용 계산
    if get_money < total_cost:
        await interaction.send("잔액이 부족하여 로또을 구매할 수 없습니다.")
        return

    # 잔액 차감
    await removemoney(user_id, total_cost)

    await interaction.response.defer()  # 응답을 미리 지연

    # 데이터베이스 파일 경로
    db_path = os.path.join('system_database', 'lotto.db')
    purchased_numbers = []  # 구매한 로또 번호를 저장할 리스트
    # 텍스트 파일 경로
    text_file_path = os.path.join('system_database', 'purchased_lotteries.txt')

    if auto:
        async with aiosqlite.connect(db_path) as db:
            for _ in range(count):
                lottery_numbers = random.sample(range(1, 46), 6)
                lottery_numbers_str = ','.join(map(str, sorted(lottery_numbers)))
                await db.execute('INSERT OR IGNORE INTO lottery (user_id, numbers) VALUES (?, ?)', (user_id, lottery_numbers_str))
                purchased_numbers.append(lottery_numbers_str)
            await db.commit()
        await interaction.send(f"{count}개의 로또가 자동으로 구매되었습니다.")
    else:
        if numbers:
            try:
                manual_numbers = list(map(int, numbers.split(',')))
                if len(manual_numbers) != 6 or len(set(manual_numbers)) != 6 or any(num < 1 or num > 45 for num in manual_numbers):
                    raise ValueError
                lottery_numbers_str = ','.join(map(str, sorted(manual_numbers)))
                async with aiosqlite.connect(db_path) as db:
                    await db.execute('INSERT OR IGNORE INTO lottery (user_id, numbers) VALUES (?, ?)', (user_id, lottery_numbers_str))
                    await db.commit()
                purchased_numbers.append(lottery_numbers_str)
                await interaction.send(f"로또 번호 {manual_numbers}이(가) 구매되었습니다.")
            except ValueError:
                await interaction.send("잘못된 번호 형식입니다. 1부터 45 사이의 중복되지 않는 6개 숫자를 입력하세요.")
        else:
            await interaction.send("수동 구매를 원하시면 로또 번호를 입력해주세요.")

    # 구매한 로또 번호를 DM으로 임베드 형태로 전송
    if purchased_numbers:
        embed = disnake.Embed(title="구매한 로또 번호", description="\n".join(purchased_numbers), color=0x00ff00)
        embed.set_footer(text="행운을 빕니다!")
        await interaction.author.send(embed=embed)

    # 구매한 복권 번호를 텍스트 파일에 저장
    if purchased_numbers:
        with open(text_file_path, 'a') as file:
            for numbers in purchased_numbers:
                file.write(f"{user_id}: {numbers}\n")

@bot.slash_command(name="이용제한", description="봇 이용을 제한합니다. [개발자전용]")
async def use_limit(ctx, user: disnake.Member = commands.Param(name="유저"), reason: str = commands.Param(name="사유", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "이용제한")
    if ctx.author.id == developer:
        if reason is None:
            reason = "없음"
        db_path = os.path.join('system_database', 'economy.db')
        economy_aiodb = await aiosqlite.connect(db_path)
        aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (user.id,))
        dbdata = await aiocursor.fetchone()
        await aiocursor.close()
        if dbdata is not None:
            if int(dbdata[0]) == 1:
                embed=disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value=f"{user.mention}는 이미 제한된 유저입니다.")
                await ctx.send(embed=embed)
            else:
                embed=disnake.Embed(title="✅ 이용제한", color=embederrorcolor)
                embed.add_field(name="대상", value=f"{user.mention}")
                embed.add_field(name="사유", value=f"{reason}")
                await ctx.send(embed=embed)
                aiocursor = await economy_aiodb.execute("UPDATE user SET tos=? WHERE id=?", (1, user.id))
                await economy_aiodb.commit()
                await aiocursor.close()
        else:
            # user 테이블에 새로운 유저 추가
            aiocursor = await economy_aiodb.execute("INSERT INTO user (id, money, tos, level, exp, lose_money, dm_on_off) VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, 0, 1, 0, 0, 0, 0))
            await economy_aiodb.commit()
            await aiocursor.close()

            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="✅ 이용제한", value=f"{user.mention}\n가입되지 않은 유저였으므로 새로 추가되었습니다.")
            await ctx.send(embed=embed)
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="제한해제", description="봇 이용제한을 해제합니다. [개발자전용]")
async def use_limit_release(ctx, user: disnake.Member = commands.Param(name="유저")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "제한해제")
    if ctx.author.id == developer:
        db_path = os.path.join('system_database', 'economy.db')
        economy_aiodb = await aiosqlite.connect(db_path)
        aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (user.id,))
        dbdata = await aiocursor.fetchone()
        await aiocursor.close()
        if dbdata is not None:
            if int(dbdata[0]) == 1:
                embed=disnake.Embed(color=embederrorcolor)
                embed.add_field(name="제한해제", value=f"{user.mention} 차단이 해제되었습니다.")
                await ctx.send(embed=embed)
                aiocursor = await economy_aiodb.execute("UPDATE user SET tos=? WHERE id=?", (0, user.id))
                await economy_aiodb.commit()
                await aiocursor.close()
            else:
                embed=disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value=f"{user.mention} 제한되지 않은 유저입니다.")
                await ctx.send(embed=embed)
        else:
            embed=disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=f"{ctx.author.mention}\n가입되지 않은 유저입니다.")
            await ctx.send(embed=embed, ephemeral=True)
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="코드추가", description="멤버쉽 코드를 추가하고 기간을 설정합니다.")
async def license_code_add(ctx: disnake.CommandInteraction, code: str = commands.Param(name="코드", choices=["gift", "reward", "general"]), date: int = commands.Param(name="기간")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "코드추가")
    if ctx.author.id == developer:
        # 기간을 일 단위로 받아서 설정
        if date <= 0:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="유효한 기간을 입력해야 합니다.")
            await ctx.send(embed=embed, ephemeral=True)
            return

        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

        if code == "gift":
            code = f"gift-{random_code}"
        elif code == "reward":
            code = f"reward-{random_code}"
        elif code == "general":
            code = f"{random_code}-{random_code}"
        else:
            print("코드추가 명령어 오류발생")
            return
        db_path = os.path.join('system_database', 'membership.db')
        economy_aiodb = await aiosqlite.connect(db_path)  # 데이터베이스 연결
        await economy_aiodb.execute("INSERT INTO license (code, day, use) VALUES (?, ?, ?)", (code, date, 0))
        await economy_aiodb.commit()

        embed = disnake.Embed(title="✅ 코드추가", color=0x00ff00)
        embed.add_field(name="코드", value=f"{code}")
        embed.add_field(name="기간", value=f"{date}")
        await ctx.send(embed=embed, ephemeral=True)
        await economy_aiodb.close()
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="코드삭제", description="멤버쉽 코드를 삭제합니다.")
async def license_code_remove(ctx: disnake.CommandInteraction, code: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "코드삭제")
    if ctx.author.id == developer:
        db_path = os.path.join('system_database', 'membership.db')
        economy_aiodb = await aiosqlite.connect(db_path)  # 데이터베이스 연결

        # 해당 코드가 존재하는지 확인
        aiocursor = await economy_aiodb.execute("SELECT * FROM license WHERE code=?", (code,))
        license_data = await aiocursor.fetchone()

        if license_data is None:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="유효하지 않은 코드입니다.")
            await ctx.send(embed=embed, ephemeral=True)
            await aiocursor.close()
            await economy_aiodb.close()
            return

        # 코드 삭제
        await economy_aiodb.execute("DELETE FROM license WHERE code=?", (code,))
        await economy_aiodb.commit()

        embed = disnake.Embed(color=0x00ff00)
        embed.add_field(name="✅ 성공", value="코드가 삭제되었습니다.")
        await ctx.send(embed=embed, ephemeral=True)

        await aiocursor.close()
        await economy_aiodb.close()
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="멤버쉽등록", description="멤버쉽 회원으로 등록하거나 기간을 연장합니다.")
async def license_code_use(ctx: disnake.CommandInteraction, code: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "멤버쉽등록")
    db_path = os.path.join('system_database', 'membership.db')
    economy_aiodb = await aiosqlite.connect(db_path)

    # license 테이블에서 code 확인
    aiocursor = await economy_aiodb.execute("SELECT use, day FROM license WHERE code=?", (code,))
    license_data = await aiocursor.fetchone()

    if license_data is None:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="유효하지 않은 코드입니다.")
        await ctx.send(embed=embed, ephemeral=True)
        await aiocursor.close()
        await economy_aiodb.close()
        return

    # use 값이 1이면 이미 사용된 코드
    if license_data[0] == 1:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="이미 사용된 코드입니다.")
        await ctx.send(embed=embed, ephemeral=True)
        await aiocursor.close()
        await economy_aiodb.close()
        return

    # 현재 날짜 계산
    current_date = datetime.now()
    additional_days = license_data[1]
    expiration_date = current_date + timedelta(days=additional_days)

    # user 테이블에서 현재 사용자 확인
    aiocursor = await economy_aiodb.execute("SELECT class, expiration_date FROM user WHERE id=?", (ctx.author.id,))
    dbdata = await aiocursor.fetchone()

    if dbdata is None:
        # 데이터가 없을 경우 비회원으로 등록
        await economy_aiodb.execute("INSERT INTO user (id, class, expiration_date, credit) VALUES (?, ?, ?, ?)", 
                                     (ctx.author.id, 1, expiration_date.strftime('%Y/%m/%d'), 30))  # 1: 회원
        await economy_aiodb.commit()
        embed = disnake.Embed(color=0x00ff00)
        embed.add_field(name="✅ 성공", value="비회원에서 회원으로 등록되었습니다.")
        await ctx.send(embed=embed, ephemeral=True)
    else:
        member_class = int(dbdata[0])
        existing_expiration_date = datetime.strptime(dbdata[1], '%Y/%m/%d')

        if member_class == 0:  # 0: 비회원
            # 비회원에서 회원으로 변경
            await economy_aiodb.execute("UPDATE user SET class = ?, expiration_date = ? WHERE id = ?", 
                                         (1, expiration_date.strftime('%Y/%m/%d'), ctx.author.id))
            await economy_aiodb.commit()
            embed = disnake.Embed(color=0x00ff00)
            embed.add_field(name="✅ 성공", value="비회원에서 회원으로 변경되었습니다.")
            await ctx.send(embed=embed, ephemeral=True)
        else:
            # 기존 만료일에 추가
            new_expiration_date = existing_expiration_date + timedelta(days=additional_days)
            await economy_aiodb.execute("UPDATE user SET expiration_date = ? WHERE id = ?", 
                                         (new_expiration_date.strftime('%Y/%m/%d'), ctx.author.id))
            await economy_aiodb.commit()
            embed = disnake.Embed(color=0x00ff00)
            embed.add_field(name="✅ 성공", value="기간이 연장되었습니다.")
            await ctx.send(embed=embed, ephemeral=True)

    # 코드 사용 처리 (use 값을 1로 업데이트)
    await economy_aiodb.execute("UPDATE license SET use = ? WHERE code = ?", (1, code))
    await economy_aiodb.commit()

    await aiocursor.close()
    await economy_aiodb.close()

@bot.slash_command(name="멤버쉽", description="현재 멤버쉽 상태를 확인합니다.")
async def check_membership_status(ctx: disnake.CommandInteraction):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "멤버쉽")
    db_path = os.path.join('system_database', 'membership.db')
    economy_aiodb = await aiosqlite.connect(db_path)

    # user 테이블에서 현재 사용자 확인
    aiocursor = await economy_aiodb.execute("SELECT class, expiration_date, credit FROM user WHERE id=?", (ctx.author.id,))
    dbdata = await aiocursor.fetchone()

    if dbdata is None:
        # 사용자 데이터가 없다면 새로 생성
        await economy_aiodb.execute("INSERT INTO user (id, class, expiration_date, credit) VALUES (?, ?, ?, ?)", 
                                      (ctx.author.id, 0, None, 5))  # 기본값으로 비회원, 만료일 없음, 크레딧 0
        await economy_aiodb.commit()

        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="회원이 아닙니다. 새로 가입되었습니다.")
        embed.add_field(name="💰 크레딧", value="5")
        await ctx.send(embed=embed, ephemeral=True)
    else:
        member_class = int(dbdata[0])
        expiration_date = dbdata[1]
        credits = dbdata[2]

        if member_class == 0:
            status = "비회원"
        elif member_class == 1:
            status = "브론즈_회원"
        elif member_class == 2:
            status = "실버_회원"
        elif member_class == 3:
            status = "다이아_회원"
        elif member_class == 4:
            status = "레전드_회원"
        elif member_class == 5:
            status = "개발자"
        else:
            print("error : 데이터값이 0, 1, 2, 3, 4, 5가 아닙니다.")

        embed = disnake.Embed(color=0x00ff00)
        embed.add_field(name=f"{ctx.author.name}님의 멤버십 📋", value=f"상태: {status}\n만료일: {expiration_date}\n💰 크레딧: {credits}")
        await ctx.send(embed=embed)

    await aiocursor.close()
    await economy_aiodb.close()

@bot.slash_command(name="가입", description="경제기능을 가입합니다.")
async def economy_join(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "가입")
    db_path = os.path.join('system_database', 'economy.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (ctx.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata == None:
        aiocursor = await economy_aiodb.execute("INSERT INTO user (id, money, tos, level, exp, lose_money, dm_on_off) VALUES (?, ?, ?, ?, ?, ?, ?)", (ctx.author.id, 0, 0, 0, 0, 0, 0))
        await economy_aiodb.commit()
        await aiocursor.close()
        await addmoney(ctx.author.id, 30000)
        embed=disnake.Embed(color=embedsuccess)
        embed.add_field(name="✅ 가입", value=f"{ctx.author.mention} 가입이 완료되었습니다.\n지원금 30,000원이 지급되었습니다.")
        await ctx.send(embed=embed)
    else:
        if int(dbdata[0]) == 1:
            embed=disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.")
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed=disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=f"{ctx.author.mention} 이미 가입된 유저입니다.")
            await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="탈퇴", description="경제기능을 탈퇴합니다.")
async def economy_secession(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "탈퇴")
    db_path = os.path.join('system_database', 'economy.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (ctx.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    
    if dbdata is not None:
        if int(dbdata[0]) == 1:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.")
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(color=0xffff00)
            embed.add_field(name="탈퇴", value="경고! 탈퇴시 모든 데이터가 **즉시 삭제**되며\n보유중인 잔액이 초기화됩니다.")
            message = await ctx.send(embed=embed, view=AuthButton(economy_aiodb, ctx.author.id))

    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value=f"{ctx.author.mention}\n가입되지 않은 유저입니다.")
        await ctx.send(embed=embed, ephemeral=True)

class AuthButton(disnake.ui.View):
    def __init__(self, economy_aiodb, author_id):
        super().__init__(timeout=None)
        self.economy_aiodb = economy_aiodb
        self.author_id = author_id
        self.closed = False  # 새로운 속성 추가

    @disnake.ui.button(label="탈퇴", style=disnake.ButtonStyle.green)
    async def 탈퇴(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        embed = disnake.Embed(color=0x00FF00)
        embed.add_field(name="탈퇴 완료!", value="탈퇴가 완료되었습니다!")
        await interaction.message.edit(embed=embed, view=None)
        aiocursor = await self.economy_aiodb.execute("DELETE FROM user WHERE id=?", (self.author_id,))
        await self.economy_aiodb.commit()
        await aiocursor.close()
        self.stop()
        button.disabled = True

    @disnake.ui.button(label="취소", style=disnake.ButtonStyle.red)
    async def 취소(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        embed = disnake.Embed(color=0x00FF00)
        embed.add_field(name="탈퇴 취소", value="탈퇴가 취소되었습니다.")
        await interaction.message.edit(embed=embed, view=None)
        self.stop()
        button.disabled = True

@bot.slash_command(name="몬스터타입설정", description="채널의 몬스터 타입을 설정합니다.")
async def set_monster_type_command(ctx, monster_type: str = commands.Param(name="타입", choices=["초원", "고수의땅", "지옥의땅"])):
    # 서버의 관리자인지 확인
    if not ctx.author.guild_permissions.manage_channels:
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value="이 명령어를 사용할 권한이 없습니다. 관리자만 사용할 수 있습니다.")
        await ctx.send(embed=embed)
        return

    server_id = str(ctx.guild.id)  # 서버 ID
    channel_id = str(ctx.channel.id)  # 채널 ID

    # 몬스터 타입 설정
    await set_monster_type(server_id, channel_id, monster_type)

    await ctx.send(f"{ctx.channel.name} 채널의 몬스터 타입이 '{monster_type}'으로 설정되었습니다.")

# 초원
weak_monsters = {
    "잉어킹": {"hp": 200, "reward": 400},
    "데구리": {"hp": 300, "reward": 500},
    "파이리": {"hp": 500, "reward": 700},
    "메타몽": {"hp": 500, "reward": 700},
    "라이츄": {"hp": 800, "reward": 1000},
    "꼬부기": {"hp": 1100, "reward": 1300},
}
# 고수의땅
strong_monsters = {
    "피카츄": {"hp": 1400, "reward": 1600},
    "리자몽": {"hp": 1700, "reward": 1900},
    "마기라스": {"hp": 2000, "reward": 2200},
    "리자드": {"hp": 2000, "reward": 2200},
    "메타그로스": {"hp": 2300, "reward": 2500},
    "메가리자몽X": {"hp": 2600, "reward": 2800},
}
# 지옥의땅
hell_monsters = {
    "지옥의벌래": {"hp": 2900, "reward": 3100},
    "저승사자": {"hp": 3200, "reward": 3400},
    "사신": {"hp": 3500, "reward": 3700},
    "지옥의드래곤": {"hp": 3800, "reward": 4000},
    "사탄": {"hp": 4100, "reward": 4300},
    "지옥의왕": {"hp": 4400, "reward": 4600},
}

sword = ["나무검", "돌검", "철검", "단단한검", "무적의검", "만용의검", "폭풍의검", "화염의검", "사신의괭이", "불의도끼"]

# 초원에서 사용할 수 없는 검 리스트
veld_restricted_swords = ["만용의검", "폭풍의검", "화염의검", "사신의괭이", "불의도끼"]
# 고수의땅에서 사용할 수 없는 검 리스트
master_restricted_swords = ["나무검", "돌검", "철검", "화염의검", "사신의괭이", "불의도끼"]
# 지옥의땅에서 사용할 수 없는 검 리스트
hell_restricted_swords = ["나무검", "돌검", "철검", "단단한검", "만용의검", "폭풍의검"]

@bot.slash_command(name="몬스터사냥", description="랜덤 몬스터를 잡습니다.")
async def catch_monster(ctx, sword_name: str = commands.Param(name="검이름", choices=sword)):
    await ctx.response.defer()  # 응답 지연

    user_id = ctx.author.id  # 사용자 ID 가져오기

    # 사용자의 인벤토리에서 칼이 있는지 확인
    sword_info = await get_user_item(user_id, sword_name)

    if sword_info is None or (isinstance(sword_info, tuple) and sword_info[1] <= 0):
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value=f"{sword_name}이(가) 인벤토리에 없습니다.")
        await ctx.send(embed=embed)
        return

    # 채널의 몬스터 타입 조회
    server_id = str(ctx.guild.id)
    channel_id = str(ctx.channel.id)
    monster_type = await get_monster_type(server_id, channel_id)

    # 초원 및 고수의 땅 제한 검사
    if (monster_type == "초원" and sword_name in veld_restricted_swords) or \
       (monster_type == "고수의땅" and sword_name in master_restricted_swords) or \
       (monster_type == "지옥의땅" and sword_name in hell_restricted_swords) or \
       (monster_type is None and sword_name in veld_restricted_swords):
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value=f"{sword_name}은(는) 해당 지역에서 사용할 수 없습니다.")
        await ctx.send(embed=embed)
        return

    # 몬스터 선택
    monsters_dict = {
        "초원": weak_monsters,
        "고수의땅": strong_monsters,
        "지옥의땅": hell_monsters
    }
    monsters = monsters_dict.get(monster_type, weak_monsters)
    monster_name = random.choice(list(monsters.keys()))
    monster_hp = monsters[monster_name]["hp"]

    # 칼의 기본 데미지 조회
    sword_damage = await get_item_damage(sword_name)
    sword_class = await get_item_class(user_id, sword_name)
    total_damage = sword_damage * sword_class  # 최종 데미지 계산

    # 초기 메시지 임베드 생성
    embed = disnake.Embed(title="몬스터와의 전투!", color=0x00ff00)
    embed.add_field(name=f"몬스터: {monster_name}", value=f"HP: {monster_hp}", inline=False)

    # 공격 버튼 생성
    attack_button = disnake.ui.Button(label="공격", style=disnake.ButtonStyle.primary)
    end_battle_button = disnake.ui.Button(label="전투 종료", style=disnake.ButtonStyle.danger)

    # 버튼 뷰 생성
    view = disnake.ui.View(timeout=None)  # 뷰의 타임아웃을 설정하지 않음
    view.add_item(attack_button)
    view.add_item(end_battle_button)

    # 메시지 전송
    message = await ctx.send(embed=embed, view=view)

    async def attack_callback(interaction):
        await interaction.response.defer()  # 응답 지연
        nonlocal monster_hp

        # 몬스터 도망 확률 체크
        if random.random() < 0.05:  # 5% 확률로 도망
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="🏃 사냥실패", value=f"{monster_name}이(가) 도망쳤습니다!")
            await interaction.followup.edit_message(embed=embed, view=None)  # 버튼 제거
            return

        # 공격 시 칼의 파괴 확률
        sword_destroy_chance = random.randint(1, 101)
        defense_item_info = await get_user_item(user_id, "파괴방어권")

        if sword_destroy_chance <= 15:  # 10% 확률로 칼이 파괴됨
            if defense_item_info and isinstance(defense_item_info, tuple) and defense_item_info[1] > 0:
                await remove_item_from_user_inventory(user_id, "파괴방어권", 1)
                embed = disnake.Embed(color=0x00ff00)
                embed.add_field(name="✅ 방어 성공", value=f"{sword_name}이(가) 파괴되지 않았습니다! '파괴방어권'이 사용되었습니다.")
                await interaction.followup.edit_message(embed=embed, view=view)
                return
            else:
                await remove_item_from_user_inventory(user_id, sword_name, 1)
                embed = disnake.Embed(color=0xff0000)
                embed.add_field(name="❌ 실패", value=f"{sword_name}이(가) 파괴되었습니다.")
                await interaction.followup.edit_message(embed=embed, view=None)
                return

        # 몬스터에게 데미지 입힘
        monster_hp -= total_damage

        if monster_hp > 0:
            embed = disnake.Embed(title="몬스터와의 전투!", color=0x00ff00)
            embed.add_field(name=f"몬스터: {monster_name}", value=f"HP: {monster_hp}", inline=False)
            await interaction.followup.edit_message(embed=embed, view=view)
        else:
            reward = monsters[monster_name]["reward"]
            await add_cash_item_count(user_id, reward)
            embed = disnake.Embed(color=0x00ff00)
            embed.add_field(name="✅ 성공", value=f"{monster_name}을(를) 처치했습니다! 보상으로 {reward}을(를) 받았습니다.")
            await interaction.followup.edit_message(embed=embed, view=None)  # 버튼 제거

    async def end_battle_callback(interaction):
        await interaction.response.defer()  # 응답 지연
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="⚔️ 전투 종료", value="전투가 종료되었습니다.")
        await interaction.followup.edit_message(embed=embed, view=None)  # 버튼 제거

    # 버튼 콜백 설정
    attack_button.callback = attack_callback
    end_battle_button.callback = end_battle_callback

@bot.slash_command(name="아이템사용", description="경험치 병을 사용하여 경험치를 증가시킵니다.")
async def use_experience_potion(ctx, count: int = commands.Param(name="개수")):
    if not await check_permissions(ctx):
        return

    await command_use_log(ctx, "경험치병사용")
    
    if not await member_status(ctx):
        return

    # 사용자의 인벤토리에서 경험치 병 수량 조회
    user_item_count = await get_user_item(ctx.author.id, "경험치 병")

    # 아이템 수량 검증
    if user_item_count is None or user_item_count <= 0:
        await send_error_embed(ctx, "경험치 병이 인벤토리에 없습니다.")
        return

    if count <= 0:
        await send_error_embed(ctx, "사용할 경험치 병의 수량은 1개 이상이어야 합니다.")
        return

    if user_item_count < count:
        await send_error_embed(ctx, "인벤토리에 요청한 수량만큼의 경험치 병이 없습니다.")
        return

    # 경험치 병의 add_exp 값을 아이템 테이블에서 조회
    experience_per_potion = await fetch_experience_per_potion()
    if experience_per_potion is None:
        await send_error_embed(ctx, "경험치 병의 경험치 정보가 없습니다.")
        return

    total_experience = experience_per_potion * count

    # 사용자 경험치 업데이트
    await add_exp(ctx.author.id, total_experience)
    await remove_item_from_user_inventory(ctx.author.id, "경험치 병", count)

    embed = disnake.Embed(color=0x00ff00, description=f"{count}개의 경험치 병을 사용하여 {total_experience} 경험치를 얻었습니다.")
    await ctx.send(embed=embed)

async def send_error_embed(ctx, error_message):
    embed = disnake.Embed(color=0xff0000, description=f"❌ 오류: {error_message}")
    await ctx.send(embed=embed)

async def fetch_experience_per_potion():
    db_path = os.path.join('system_database', 'economy.db')
    async with aiosqlite.connect(db_path) as economy_aiodb:
        async with economy_aiodb.cursor() as aiocursor:
            await aiocursor.execute("SELECT add_exp FROM item WHERE name = ?", ("경험치 병",))
            exp_info = await aiocursor.fetchone()
            return exp_info[0] if exp_info else None

class ItemView(disnake.ui.View):
    def __init__(self, data, per_page=5):
        super().__init__(timeout=None)
        self.data = data
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(data) - 1) // per_page
        self.message = None
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):
        embed = disnake.Embed(title="아이템 목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page

        for item in self.data[start:end]:
            if len(item) == 4:
                name, price, damage, add_exp = item
                embed.add_field(name=name, value=f"가격: {price:,}원 | 피해: {damage} | 경험치: {add_exp}", inline=False)
            else:
                print(f"아이템 데이터 오류: {item}")

        embed.set_footer(text=f"페이지 {self.current_page + 1}/{self.max_page + 1} | 마지막 업데이트: {self.last_updated}")
        return embed

class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: ItemView = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_message(interaction)

class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: ItemView = self.view
        if view.current_page < view.max_page:
            view.current_page += 1
            await view.update_message(interaction)

@bot.slash_command(name="아이템목록", description="아이템 목록을 확인합니다.")
async def item_list(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "아이템목록")
    data = await get_items()  # 아이템 정보를 가져옴
    view = ItemView(data)

    # 태스크가 이미 실행 중인지 확인
    if view_update3.is_running():
        view_update3.stop()  # 실행 중이면 중지

    embed = await view.create_embed()
    view.message = await ctx.send(embed=embed, view=view)
    view_update3.start(view)  # 태스크 시작

@tasks.loop(seconds=20)
async def view_update3(view: ItemView):
    view.data = await get_items()  # 아이템 정보를 다시 가져옴
    view.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await view.update_message()

# 강화 확률을 정의합니다.
upgrade_chances = {
    1: 0.85,
    2: 0.80,
    3: 0.75,
    4: 0.70,
    5: 0.65,
    6: 0.60,
    7: 0.50,
    8: 0.40,
    9: 0.30,
    10: 0.20,
}

@bot.slash_command(name="강화", description="아이템을 강화합니다.")
async def upgrade_item(ctx, item_name: str):
    if not await check_permissions(ctx):
        return
    
    await command_use_log(ctx, "아이템강화")
    if not await member_status(ctx):
        return

    # 사용자 인벤토리에서 아이템 정보 가져오기
    item_info = await get_user_item_class(ctx.author.id, item_name)

    if not item_info:
        return await send_error_message(ctx, f"{item_name} 아이템이 인벤토리에 없습니다.")

    current_class = item_info[1]  # 현재 강화 등급
    if current_class >= 10:
        return await send_error_message(ctx, "이미 최대 강화 등급(10강)입니다.")

    # 강화 비용 계산
    upgrade_cost = (current_class + 1) * 100 + 100

    # 사용자 캐시 조회
    user_cash = await get_cash_item_count(ctx.author.id)
    if user_cash < upgrade_cost:
        return await send_error_message(ctx, "캐시가 부족하여 강화할 수 없습니다.")

    # 캐시 차감
    await remove_cash_item_count(ctx.author.id, upgrade_cost)

    # 버튼 생성
    view = create_upgrade_view(ctx, item_name, current_class, upgrade_cost)

    # 초기 메시지 전송
    embed = create_upgrade_embed(item_name, current_class, upgrade_cost)
    await ctx.send(embed=embed, view=view)

async def create_upgrade_view(ctx, item_name, current_class, upgrade_cost):
    upgrade_button = disnake.ui.Button(label="강화", style=disnake.ButtonStyle.primary)
    cancel_button = disnake.ui.Button(label="강화 취소", style=disnake.ButtonStyle.danger)

    view = disnake.ui.View()
    view.add_item(upgrade_button)
    view.add_item(cancel_button)

    # 버튼 콜백 설정
    upgrade_button.callback = lambda interaction: upgrade_callback(interaction, ctx, item_name, current_class, upgrade_button, view)
    cancel_button.callback = lambda interaction: cancel_callback(interaction, ctx)

    return view

async def create_upgrade_embed(item_name, current_class, upgrade_cost):
    embed = disnake.Embed(title="아이템 강화", color=0x00ffff)
    embed.add_field(name="강화할 아이템", value=item_name, inline=False)
    embed.add_field(name="현재 강화 등급", value=f"{current_class}강", inline=False)
    embed.add_field(name="비용", value=f"{upgrade_cost} 캐시", inline=False)
    return embed

async def upgrade_callback(interaction, ctx, item_name, current_class, upgrade_button, view):
    if interaction.user.id != ctx.author.id:
        return await send_error_message(interaction, "이 버튼은 호출자만 사용할 수 있습니다.")

    # 강화 중 파괴 확률 체크
    if await handle_destruction(interaction, ctx, item_name):
        return

    # 강화 성공 확률 확인
    success_chance = upgrade_chances.get(current_class + 1)
    if success_chance is None:
        return await send_error_message(interaction, "강화 성공 확률 정보를 찾을 수 없습니다.")

    if random.random() <= success_chance:
        await handle_upgrade_success(interaction, ctx, item_name, current_class, view)
    else:
        await handle_upgrade_failure(interaction, ctx, item_name, current_class, view)

async def handle_destruction(interaction, ctx, item_name):
    destruction_chance = random.random()
    if destruction_chance <= 0.05:  # 5% 확률로 파괴
        defense_item_info = await get_user_item(ctx.author.id, "파괴방어권")
        if defense_item_info and isinstance(defense_item_info, tuple) and defense_item_info[1] > 0:
            await remove_item_from_user_inventory(ctx.author.id, "파괴방어권", 1)
            embed = disnake.Embed(color=0x00ff00)
            embed.add_field(name="✅ 방어 성공", value=f"{item_name} 아이템이 파괴되지 않았습니다! '파괴방어권'이 사용되었습니다.")
            await interaction.followup.edit_message(embed=embed)
            return True  # 방어 성공
        await remove_item_from_user_inventory(ctx.author.id, item_name, 1)
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 아이템 파괴", value=f"{item_name} 아이템이 파괴되었습니다.")
        await interaction.followup.edit_message(embed=embed)
        return True  # 아이템 파괴
    return False  # 파괴되지 않음

async def handle_upgrade_success(interaction, ctx, item_name, current_class, view):
    new_class = current_class + 1
    await update_item_class(ctx.author.id, item_name, new_class)
    embed = disnake.Embed(color=0x00ff00)
    embed.add_field(name="✅ 강화 성공", value=f"{item_name} 아이템이 {new_class}강으로 강화되었습니다.")
    embed.add_field(name="현재 강화 등급", value=f"{new_class}강", inline=False)
    embed.add_field(name="비용", value=f"{(new_class + 1) * 100 + 100} 캐시", inline=False)
    await interaction.followup.edit_message(embed=embed, view=view)

async def handle_upgrade_failure(interaction, ctx, item_name, current_class, view):
    await update_item_class(ctx.author.id, item_name, current_class)
    embed = disnake.Embed(color=0xff0000)
    embed.add_field(name="❌ 강화 실패", value=f"{item_name} 아이템의 강화에 실패했습니다.")
    embed.add_field(name="현재 강화 등급", value=f"{current_class}강", inline=False)
    embed.add_field(name="비용", value=f"{(current_class + 1) * 100 + 100} 캐시", inline=False)
    embed.add_field(name="팁", value="다시 시도하거나 다른 아이템을 강화해 보세요!", inline=False)
    await interaction.followup.edit_message(embed=embed, view=view)

async def cancel_callback(interaction, ctx):
    if interaction.user.id != ctx.author.id:
        return await send_error_message(interaction, "이 버튼은 호출자만 사용할 수 있습니다.")

    embed = disnake.Embed(color=0xff0000)
    embed.add_field(name="⚔️ 강화 취소", value="강화가 취소되었습니다.")
    await interaction.followup.edit_message(embed=embed, view=None)

async def send_error_message(ctx, message):
    embed = disnake.Embed(color=0xff0000)
    embed.add_field(name="❌ 오류", value=message)
    await ctx.send(embed=embed)

@bot.slash_command(name="아이템관리", description="아이템을 추가하거나 삭제할 수 있습니다. [개발자전용]")
async def item_management(ctx, item_name: str, choice: str = commands.Param(name="선택", choices=["추가", "삭제"]), item_price: float = commands.Param(name="가격", default=None), item_damage: int = commands.Param(name="데미지", default=None), item_exp: int = commands.Param(name="경험치", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "아이템관리")
    if ctx.author.id == developer:
        if choice == "추가":
            await add_item(item_name, item_price, item_damage, item_exp)
            embed = disnake.Embed(color=embedsuccess)
            embed.add_field(name="✅ 성공", value=f"{item_name} 아이템을 추가하였습니다.\n가격: {item_price:,} 원\n데미지: {item_damage}\n경험치: {item_exp}")
            await ctx.send(embed=embed)
        elif choice == "삭제":
            await remove_item(item_name)
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="🗑️ 삭제", value=f"{item_name} 아이템을 삭제하였습니다.")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="아이템거래", description="아이템을 구매 또는 판매할 수 있습니다.")
async def item_trading(ctx, item_name: str = commands.Param(name="이름"), choice: str = commands.Param(name="선택", choices=["구매", "판매"]), count: int = commands.Param(name="개수", default=1)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "아이템거래")
    if not await member_status(ctx):
        return
    
    embed = disnake.Embed(color=0x00ff00)
    
    try:
        # 음수 거래 방지
        if count <= 0:
            raise ValueError("거래할 아이템 수량은 1개 이상이어야 합니다.")

        item_info = await get_item_info(item_name)  # 아이템 정보를 가져오는 함수
        if item_info is None:
            raise ValueError(f"{item_name} 아이템은 존재하지 않습니다.")
        
        item_price = item_info['price']  # 아이템의 가격
        total_price = item_price * count

        if choice == "구매":
            if item_name in ["나무검", "돌검", "철검", "단단한검", "무적의검", "만용의검", "폭풍의검", "화염의검", "사신의괭이", "불의도끼"]:
                user_item_quantity = await get_user_item_count(ctx.author.id, item_name)  # 사용자의 아이템 수량 조회
                if user_item_quantity >= 1:
                    raise ValueError(f"{item_name}은(는) 이미 1개 보유하고 있습니다. 추가 구매할 수 없습니다.")
                count = 1  # 수량을 1로 설정
                total_price = item_price  # 총 가격도 1개 가격으로 설정

            user_balance = await getmoney(ctx.author.id)  # 사용자의 잔액 조회
            if user_balance < total_price:
                raise ValueError("잔액이 부족합니다.")

            await removemoney(ctx.author.id, total_price)  # 잔액 차감
            await add_item_to_user_inventory(ctx.author.id, item_name, count)  # 인벤토리에 아이템 추가
            
            embed.title = "아이템 구매 완료"
            embed.add_field(name="아이템 이름", value=item_name, inline=False)
            embed.add_field(name="구매 수량", value=f"{count:,}개", inline=False)
            embed.add_field(name="총 구매 가격", value=f"{total_price:,}원", inline=False)

        elif choice == "판매":
            user_item_quantity = await get_user_item_count(ctx.author.id, item_name)  # 사용자의 아이템 수량 조회
            if user_item_quantity < count:
                raise ValueError("판매할 수량이 인벤토리보다 많습니다.")

            await remove_item_from_user_inventory(ctx.author.id, item_name, count)  # 인벤토리에서 아이템 제거
            await addmoney(ctx.author.id, total_price)  # 잔액에 판매 금액 추가
            
            embed.title = "아이템 판매 완료"
            embed.add_field(name="아이템 이름", value=item_name, inline=False)
            embed.add_field(name="판매 수량", value=f"{count:,}개", inline=False)
            embed.add_field(name="총 판매 가격", value=f"{total_price:,}원", inline=False)

        await ctx.send(embed=embed)
    except ValueError as e:
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value=str(e))
        await ctx.send(embed=embed)

class ItemView2(disnake.ui.View):
    def __init__(self, items, per_page=5):
        super().__init__(timeout=None)
        self.items = items
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(items) - 1) // per_page
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):
        embed = disnake.Embed(title="인벤토리 📦", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page

        if not self.items:
            embed.add_field(name="❌ 오류", value="보유하고 있는 아이템이 없습니다.")
            return embed

        for item_name, quantity, class_value in self.items[start:end]:
            embed.add_field(name=item_name, value=f"수량: {quantity:,}개, {class_value}강", inline=False)

        embed.add_field(name="", value=f"📄 페이지 {self.current_page + 1}/{self.max_page + 1}", inline=False)
        return embed

@bot.slash_command(name="인벤토리", description="보유 중인 아이템을 확인합니다.")
async def inventory(ctx: disnake.CommandInteraction):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "인벤토리")
    if not await member_status(ctx):
        return

    items = await get_user_inventory(ctx.author.id)  # 사용자의 인벤토리 아이템을 가져오는 함수

    # 사용자 이름 가져오기
    user_name = ctx.author.name

    embed = disnake.Embed(title=f"{user_name}의 인벤토리 📦", color=0x00ff00)

    if not items:
        embed.add_field(name="❌ 오류", value="보유하고 있는 아이템이 없습니다.")
        await ctx.send(embed=embed)
    else:
        # 아이템 정보를 담고 있는 ItemView 생성
        view = ItemView2(items)

        # 초기 임베드 생성 및 메시지 전송
        view.message = await ctx.send(embed=await view.create_embed(), view=view)


class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: ItemView2 = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_message(interaction)


class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: ItemView2 = self.view
        if view.current_page < view.max_page:
            view.current_page += 1
            await view.update_message(interaction)

class CoinView1(disnake.ui.View):
    def __init__(self, data, per_page=5):
        super().__init__(timeout=None)
        self.data = data
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(data) - 1) // per_page
        self.message = None
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):
        embed = disnake.Embed(title="코인목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page
        for name, price in self.data[start:end]:
            embed.add_field(name=name, value=f"{price:,}원", inline=False)
        embed.set_footer(text=f"페이지 {self.current_page + 1}/{self.max_page + 1} | 마지막 업데이트: {self.last_updated}")
        return embed

class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: CoinView1 = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_message(interaction)

class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: CoinView1 = self.view
        if view.current_page < view.max_page:
            view.current_page += 1
            await view.update_message(interaction)

@bot.slash_command(name="코인목록", description="상장된 가상화폐를 확인합니다.")
async def coin_list(ctx):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "코인목록")
    data = await getcoin()
    view = CoinView1(data)

    # 태스크가 이미 실행 중인지 확인
    if view_update2.is_running():
        view_update2.stop()  # 실행 중이면 중지

    embed = await view.create_embed()
    view.message = await ctx.send(embed=embed, view=view)
    view_update2.start(view)  # 태스크 시작

@tasks.loop(seconds=20)
async def view_update2(view: CoinView1):
    view.data = await getcoin()
    view.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await view.update_message()

@bot.slash_command(name="가상화폐관리", description="가상화폐을 추가하거나 삭제할 수 있습니다. [개발자전용]")
async def coin_management(ctx, _name: str, choice: str = commands.Param(name="선택", choices=["추가", "삭제"]), _price: float = commands.Param(name="가격", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "가상화폐관리")
    if ctx.author.id == developer:
        if choice == "추가":
            await addcoin(_name, _price)
            price = int(_price)
            embed = disnake.Embed(color=embedsuccess)
            embed.add_field(name="✅ 성공", value=f"{_name} 가상화폐을 {price:,} 가격으로 추가하였습니다.")
            await ctx.send(embed=embed)
        elif choice == "삭제":
            await removecoin(_name)
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="🗑️ 삭제", value=f"{_name} 가상화폐을 삭제하였습니다.")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

class CoinView(disnake.ui.View):
    def __init__(self, coins, per_page=5):
        super().__init__(timeout=None)
        self.coins = coins
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(coins) - 1) // per_page
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()  # 비동기 함수 호출
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):  # 비동기 함수로 변경
        embed = disnake.Embed(title=f"가상화폐 목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page
        total_value = 0  # 총 가격 초기화

        for name, count in self.coins[start:end]:
            coin_price = next((price for coin_name, price in await getcoin() if coin_name == name), None)
            if coin_price is None:
                embed.add_field(name=name, value=f"{count}개 (현재 가격 정보를 가져오지 못했습니다.)", inline=False)
            else:
                total_value += coin_price * count  # 총 가격 계산
                embed.add_field(name=name, value=f"가격: {coin_price:,} 원 | 보유 수량: {count:,}개", inline=False)

        embed.add_field(name="", value=f"📄 페이지 {self.current_page + 1}/{self.max_page + 1}", inline=False)

        return embed


class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: CoinView = self.view
        if view.current_page > 0:
            view.current_page -= 1
            await view.update_message(interaction)


class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: CoinView = self.view
        if view.current_page < view.max_page:
            view.current_page += 1
            await view.update_message(interaction)


@bot.slash_command(name="코인지갑", description="보유중인 가상화폐를 확인합니다.")
async def coin_wallet(ctx: disnake.CommandInteraction):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "가상화폐통장")
    if not await member_status(ctx):
        return
    coins = await getuser_coin(ctx.author.id)

    # 사용자 이름 가져오기
    user_name = ctx.author.name

    embed = disnake.Embed(title=f"{user_name}의 가상화폐통장 💰", color=0x00ff00)

    if not coins:
        embed.add_field(name="❌ 오류", value="보유하고 있는 가상화폐가 없습니다.")
        await ctx.send(embed=embed)
    else:
        # 가상화폐 정보를 담고 있는 CoinView 생성
        view = CoinView(coins)

        # 초기 임베드 생성 및 메시지 전송
        view.message = await ctx.send(embed=await view.create_embed(), view=view)

@bot.slash_command(name="코인거래", description="가상화폐를 구매 또는 판매할 수 있습니다.")
async def coin_trading(ctx, _name: str = commands.Param(name="이름"), choice: str = commands.Param(name="선택", choices=["구매", "판매"]), _count: int = commands.Param(name="개수")):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "가상화폐거래")
    if not await member_status(ctx):
        return
    
    embed = disnake.Embed(color=0x00ff00)
    
    try:
        # 음수 거래 방지
        if _count <= 0:
            raise ValueError("거래할 가상화폐 수량은 1개 이상이어야 합니다.")

        coins = await getcoin()
        coin_info = next((price for name, price in coins if name == _name), None)

        if coin_info is None:
            raise ValueError(f"{_name} 가상화폐는 존재하지 않습니다.")
        else:
            coin_price = coin_info

        total_price = coin_price * _count
        
        if choice == "구매":
            await adduser_coin(ctx.author.id, _name, _count)
            embed.title = "가상화폐 구매 완료"
            embed.add_field(name="가상화폐 이름", value=_name, inline=False)
            embed.add_field(name="구매 수량", value=f"{_count:,}개", inline=False)
            await add_exp(ctx.author.id, round((total_price * 0.5) / 1000))
            embed.add_field(name="총 구매 가격", value=f"{total_price:,}원", inline=False)

        elif choice == "판매":
            await removeuser_coin(ctx.author.id, _name, _count)
            embed.title = "가상화폐 판매 완료"
            embed.add_field(name="가상화폐 이름", value=_name, inline=False)
            embed.add_field(name="판매 수량", value=f"{_count:,}개", inline=False)
            await add_exp(ctx.author.id, round((total_price * 0.5) / 1000))
            embed.add_field(name="총 판매 가격", value=f"{total_price:,}원", inline=False)

        await ctx.send(embed=embed)
    except ValueError as e:
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value=str(e))
        await ctx.send(embed=embed)

class StockView1(disnake.ui.View):
    def __init__(self, data, per_page=5):
        super().__init__(timeout=None)
        self.data = data
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(data) - 1) // per_page
        self.message = None
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):
        embed = disnake.Embed(title="주식목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page
        for name, price in self.data[start:end]:
            embed.add_field(name=name, value=f"{price:,}원", inline=False)
        embed.set_footer(text=f"페이지 {self.current_page + 1}/{self.max_page + 1} | 마지막 업데이트: {self.last_updated}")
        return embed

class PreviousButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="이전", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: StockView1 = self.view
        view.current_page -= 1
        await view.update_message(interaction)

class NextButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="다음", style=disnake.ButtonStyle.primary)

    async def callback(self, interaction: disnake.Interaction):
        view: StockView1 = self.view
        view.current_page += 1
        await view.update_message(interaction)

@bot.slash_command(name="주식목록", description="상장된 주식을 확인합니다.")
async def stock_list(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "주식목록")
    data = await getstock()
    view = StockView1(data)
    embed = await view.create_embed()
    view.message = await ctx.send(embed=embed, view=view)
    view_update1.start(view)

@tasks.loop(seconds=20)
async def view_update1(view:StockView1):
    view.data = await getstock()
    view.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await view.update_message()

@bot.slash_command(name="주식관리", description="주식을 추가하거나 삭제할 수 있습니다. [개발자전용]")
async def stock_management(ctx, _name: str, choice: str = commands.Param(name="선택", choices=["추가", "삭제"]), _price: float = commands.Param(name="가격", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "주식관리")
    if ctx.author.id == developer:
        if choice == "추가":
            await addstock(_name, _price)
            price = int(_price)
            embed = disnake.Embed(color=embedsuccess)
            embed.add_field(name="✅ 성공", value=f"{_name} 주식을 {price:,} 가격으로 추가하였습니다.")
            await ctx.send(embed=embed)
        elif choice == "삭제":
            await removestock(_name)
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="🗑️ 삭제", value=f"{_name} 주식을 삭제하였습니다.")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

class StockView(disnake.ui.View):
    def __init__(self, stocks, per_page=5):
        super().__init__(timeout=None)
        self.stocks = stocks
        self.per_page = per_page
        self.current_page = 0
        self.max_page = (len(stocks) - 1) // per_page
        self.message = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousButton())
        if self.current_page < self.max_page:
            self.add_item(NextButton())

    async def update_message(self, interaction=None):
        embed = await self.create_embed()  # 비동기 함수 호출
        self.update_buttons()
        if interaction:
            await interaction.followup.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)

    async def create_embed(self):  # 비동기 함수로 변경
        embed = disnake.Embed(title=f"주식 목록", color=0x00ff00)
        start = self.current_page * self.per_page
        end = start + self.per_page
        total_value = 0  # 총 가격 초기화

        for name, count in self.stocks[start:end]:
            stock_price = await get_stock_price(name)  # 주식 가격 가져오기
            if stock_price is None:
                embed.add_field(name=name, value=f"{count}개 (현재 가격 정보를 가져오지 못했습니다.)", inline=False)
            else:
                embed.add_field(name=name, value=f"가격: {stock_price:,} 원 | 보유 수량: {count:,}개", inline=False)

        embed.add_field(name="", value=f"📄 페이지 {self.current_page + 1}/{self.max_page + 1}", inline=False)

        return embed

def get_stock_data(stock_name):
    # 데이터베이스에 연결
    db_path = os.path.join('system_database', 'economy.db')
    conn = aiosqlite.connect(db_path)
    cursor = conn.cursor()

    try:
        # 주식 정보를 가져오는 쿼리 실행
        cursor.execute("SELECT price FROM stock WHERE name = ?", (stock_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]  # 가격 반환
        else:
            return None  # 주식이 없으면 None 반환
    finally:
        conn.close()  # 연결 종료
async def get_stock_price(stock_name):
    # 주식 심볼을 대문자로 변환
    stock_symbol = stock_name.upper()
    
    # 데이터베이스에서 주식 가격 가져오기
    stock_price = get_stock_data(stock_symbol)
    
    return stock_price  # 주식 가격 반환

async def getuser_stock(user_id):
    stocks = await get_stock_data(user_id)
    if not stocks:
        return None  # 주식이 없으면 None 반환
    return stocks

@bot.slash_command(name="주식통장", description="보유중인 주식을 확인합니다.")
async def stock_wallet(ctx: disnake.CommandInteraction):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "주식통장")
    if not await member_status(ctx):
        return

    stocks = await getuser_stock(ctx.author.id)

    user_name = ctx.author.name

    if not stocks:
        embed = disnake.Embed(title=f"{user_name}의 주식통장 💰", color=0x00ff00)
        embed.add_field(name="❌ 오류", value="보유하고 있는 주식이 없습니다.")
        embed.add_field(name="💵 총 가격", value="0 원", inline=False)
        await ctx.send(embed=embed)
    else:
        view = StockView(stocks)
        view.message = await ctx.send(embed=await view.create_embed(), view=view)

@bot.slash_command(name="주식거래", description="주식을 구매 또는 판매할 수 있습니다.")
async def stock_trading(ctx, _name: str = commands.Param(name="이름"), choice: str = commands.Param(name="선택", choices=["구매", "판매"]), _count: int = commands.Param(name="개수")):
    await ctx.response.defer()
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "주식거래")
    if not await member_status(ctx):
        return
    
    embed = disnake.Embed(color=0x00ff00)
    
    try:
        # 음수 거래 방지
        if _count <= 0:
            raise ValueError("거래할 주식 수량은 1개 이상이어야 합니다.")

        stocks = await getstock()
        stock_info = next((price for name, price in stocks if name == _name), None)

        if stock_info is None:
            raise ValueError(f"{_name} 주식은 존재하지 않습니다.")
        else:
            stock_price = stock_info

        total_price = stock_price * _count
        
        if choice == "구매":
            await adduser_stock(ctx.author.id, _name, _count)
            embed.title = "주식 구매 완료"
            embed.add_field(name="주식 이름", value=_name, inline=False)
            embed.add_field(name="구매 수량", value=f"{_count:,}개", inline=False)
            await add_exp(ctx.author.id, round((total_price * 0.5) / 1000))
            embed.add_field(name="총 구매 가격", value=f"{total_price:,}원", inline=False)

        elif choice == "판매":
            await removeuser_stock(ctx.author.id, _name, _count)
            embed.title = "주식 판매 완료"
            embed.add_field(name="주식 이름", value=_name, inline=False)
            embed.add_field(name="판매 수량", value=f"{_count:,}개", inline=False)
            await add_exp(ctx.author.id, round((total_price * 0.5) / 1000))
            embed.add_field(name="총 판매 가격", value=f"{total_price:,}원", inline=False)

        await ctx.send(embed=embed)
    except ValueError as e:
        embed = disnake.Embed(color=0xff0000)
        embed.add_field(name="❌ 오류", value=str(e))
        await ctx.send(embed=embed)

@bot.slash_command(name="서버설정_채널", description="채널설정(로그채널 및 기타채널을 설정합니다) [관리자전용]")
async def server_set(ctx, kind: str = commands.Param(name="종류", choices=["공지채널", "처벌로그", "입장로그", "퇴장로그", "인증채널"]), channel: disnake.TextChannel = commands.Param(name="채널")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "서버설정_채널")
    
    if ctx.author.guild_permissions.manage_messages:
        try:
            embed = await handle_database(ctx, kind, channel.id)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="오류 발생", value=f"데이터베이스 연결 중 오류가 발생했습니다: {e}")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="서버설정_역할", description="역할설정(인증역할 및 기타역할을 설정합니다) [관리자전용]")
async def server_set_role(ctx, kind: str = commands.Param(name="종류", choices=["인증역할"]), role: disnake.Role = commands.Param(name="역할")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "서버설정_역할")
    
    if ctx.author.guild_permissions.manage_messages:
        try:
            embed = await handle_database(ctx, kind, role.id, is_role=True)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="오류 발생", value=f"데이터베이스 연결 중 오류가 발생했습니다: {e}")
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행 가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="서버정보", description="설정되있는 로그채널을 확인할수있습니다. [관리자전용]")
async def server_info(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "서버정보")
    if ctx.author.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(ctx)
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT * FROM 설정")
        dat = await aiocursor.fetchone()
        await aiocursor.close()
        embed = disnake.Embed(title="서버설정", color=embedcolor)
        
        if dat:
            # 공지 채널
            if dat[0] is not None:
                announcement_channel = ctx.guild.get_channel(int(dat[0]))
                if announcement_channel:  # 채널이 존재하는지 확인
                    embed.add_field(name="공지채널", value=f"<#{announcement_channel.id}>", inline=False)
                else:
                    embed.add_field(name="공지채널", value="채널을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="공지채널", value="설정되지 않음", inline=False)

            # 처벌 로그 채널
            if dat[1] is not None:
                punishment_log_channel = ctx.guild.get_channel(int(dat[1]))
                if punishment_log_channel:
                    embed.add_field(name="처벌로그", value=f"<#{punishment_log_channel.id}>", inline=False)
                else:
                    embed.add_field(name="처벌로그", value="채널을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="처벌로그", value="설정되지 않음", inline=False)

            # 입장 로그 채널
            if dat[2] is not None:
                entry_log_channel = ctx.guild.get_channel(int(dat[2]))
                if entry_log_channel:
                    embed.add_field(name="입장로그", value=f"<#{entry_log_channel.id}>", inline=False)
                else:
                    embed.add_field(name="입장로그", value="채널을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="입장로그", value="설정되지 않음", inline=False)

            # 퇴장 로그 채널
            if dat[3] is not None:
                exit_log_channel = ctx.guild.get_channel(int(dat[3]))
                if exit_log_channel:
                    embed.add_field(name="퇴장로그", value=f"<#{exit_log_channel.id}>", inline=False)
                else:
                    embed.add_field(name="퇴장로그", value="채널을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="퇴장로그", value="설정되지 않음", inline=False)

            # 인증 역할
            if dat[4] is not None:
                auth_role = ctx.guild.get_role(int(dat[4]))
                if auth_role:
                    embed.add_field(name="인증역할", value=f"<@&{auth_role.id}>", inline=False)
                else:
                    embed.add_field(name="인증역할", value="역할을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="인증역할", value="설정되지 않음", inline=False)

            # 인증 채널
            if dat[5] is not None:
                exit_log_channel = ctx.guild.get_channel(int(dat[5]))
                if exit_log_channel:
                    embed.add_field(name="인증채널", value=f"<#{exit_log_channel.id}>")
                else:
                    embed.add_field(name="인증채널", value="채널을 찾을 수 없음")
            else:
                embed.add_field(name="인증채널", value="설정되지 않음")
        
        await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="정보", description="봇의 실시간 상태와 정보를 알 수 있습니다.")
async def bot_info(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "정보")

    # 응답 지연
    await ctx.response.defer()

    # 핑 측정을 위한 웹소켓 연결 함수
    def ping_websocket():
        start_time = time.time()
        ws = None  # ws 변수를 None으로 초기화
        try:
            ws = websocket.create_connection("wss://gateway.discord.gg/?v=9&encoding=json")  # Discord Gateway URL
            ws.send('{"op": 1, "d": null}')  # Ping 요청
            ws.recv()  # 응답 대기
            end_time = time.time()
            return (end_time - start_time) * 1000  # 밀리초로 변환
        except Exception as e:
            print(f"웹소켓 오류: {e}")
            return None
        finally:
            if ws is not None:
                ws.close()

    # ThreadPoolExecutor를 사용하여 웹소켓 핑 측정
    with ThreadPoolExecutor() as executor:
        ping_time = await bot.loop.run_in_executor(executor, ping_websocket)

    if ping_time is None:
        ping_time = float('inf')  # 핑 측정 실패 시 최대값으로 설정

    # 응답 시간에 따라 임베드 색상 및 메시지 결정
    if ping_time < 100:
        embed_color = 0x00ff00  # 초록색 (좋음)
        status = "응답 속도가 매우 좋습니다! 🚀"
    elif ping_time < 300:
        embed_color = 0xffff00  # 노란색 (보통)
        status = "응답 속도가 좋습니다! 😊"
    elif ping_time < 1000:
        embed_color = 0xffa500  # 주황색 (나쁨)
        status = "응답 속도가 느립니다. 😕"
    else:
        embed_color = 0xff0000  # 빨간색 (매우 나쁨)
        status = "응답 속도가 매우 느립니다! ⚠️"

    embed = disnake.Embed(title="봇 정보", color=embed_color)
    embed.add_field(name="서버수", value=f"{len(bot.guilds)}", inline=True)
    embed.add_field(name="업타임", value=f"{get_uptime()}", inline=True)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="서포트서버", value=f"[support]({sec.support_server_url})", inline=True)
    embed.add_field(name="개발자", value=f"{sec.developer_name}", inline=True)

    # CPU 정보 불러오기
    uname_info = platform.uname()
    memory_info = psutil.virtual_memory()

    total_memory = f"{memory_info.total / (1024 ** 3):.2f}"
    used_memory = f"{memory_info.used / (1024 ** 3):.2f}"
    percent_memory = memory_info.percent

    # 서버 시간
    server_date = datetime.now()
    embed.add_field(name="시스템 정보", value=f"```python {platform.python_version()}\ndiscord.py {version('discord.py')}\ndisnake {version('disnake')}\nCPU : {cpu_info['brand_raw']}\nOS : {uname_info.system} {uname_info.release}\nMemory : {used_memory}GB / {total_memory}GB ({percent_memory}%)```\n응답속도 : {int(ping_time)}ms / {status}\n{server_date.strftime('%Y년 %m월 %d일 %p %I:%M').replace('AM', '오전').replace('PM', '오후')}", inline=False)

    # 응답 전송
    await ctx.edit_original_response(embed=embed)

@bot.slash_command(name="개발자_공지", description="모든서버에게 공지를 전송합니다. [개발자전용]")
async def developer_notification(ctx, *, content: str = commands.Param(name="내용")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "개발자_공지")
    if ctx.author.id == developer:
        for guild in bot.guilds:
            server_remove_date = datetime.now()
            embed1 = disnake.Embed(title="개발자 공지", description=f"```{content}```", color=embedcolor)
            embed1.set_footer(text=f'To. {sec.developer_company}({ctx.author.name})\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
            
            chan = None  # 채널 변수를 초기화합니다.
            for channel in guild.text_channels:
                try:
                    if channel.topic and sec.notification_topic in channel.topic:  # topic이 None이 아닐 때 확인
                        chan = channel
                        break  # 첫 번째 채널을 찾으면 루프를 종료합니다.
                except:
                    pass
            
            try:
                if chan and chan.permissions_for(guild.me).send_messages:
                    await chan.send(embed=embed1)
                else:
                    raise ValueError("채널이 없거나 메시지 전송 권한이 없습니다.")
            except:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        embed1.set_footer(text=f'To. CodeStone({ctx.author.name})\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
                        try:
                            await channel.send(embed=embed1)
                        except Exception as e:
                            print(f"Error sending message to {channel.name}: {e}")  # 예외 로그 추가
                        break

        embed = disnake.Embed(title="공지 업로드 완료!", color=embedsuccess)
        await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="슬로우모드", description="채팅방에 슬로우모드를 적용합니다. [관리자전용]")
async def slowmode(ctx, time: int = commands.Param(name="시간", description="시간(초)")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "슬로우모드")
    if ctx.author.guild_permissions.manage_messages:
        if time == 0:
            embed = disnake.Embed(title="\✅슬로우모드를 껐어요.", color=embedsuccess)
            await ctx.send(embed=embed)
            await ctx.channel.edit(slowmode_delay=0)
            return
        elif time > 21600:
            embed = disnake.Embed(title="\❌슬로우모드를 6시간 이상 설정할수 없어요.", color=embederrorcolor)
            await ctx.send(embed=embed, ephemeral=True)
            return
        else:
            await ctx.channel.edit(slowmode_delay=time)
            embed = disnake.Embed(title=f"\✅ 성공적으로 슬로우모드를 {time}초로 설정했어요.", color=embedsuccess)
            await ctx.send(embed=embed)
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="청소", description="메시지를 삭제합니다. [관리자전용]")
async def clear(ctx, num: int = commands.Param(name="개수")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "청소")
    if ctx.author.guild_permissions.manage_messages:
        num = int(num)
        await ctx.channel.purge(limit=num)
        embed = disnake.Embed(color=embedsuccess)
        embed.add_field(name=f"{num}개의 메시지를 지웠습니다.", value="")
        await ctx.send(embed=embed)
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="공지", description="서버에 공지를 전송합니다. [관리자전용]")
async def notification(ctx, *, content: str = commands.Param(name="내용")):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "공지")
    if ctx.author.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(ctx)
        else:
            aiodb = await aiosqlite.connect(db_path)
            aiocursor = await aiodb.execute("SELECT 공지채널 FROM 설정")
            설정_result = await aiocursor.fetchone()
            await aiocursor.close()
            
            if 설정_result:
                공지채널_id = 설정_result[0]
                공지채널 = bot.get_channel(공지채널_id)
            
            if 공지채널:
                for guild in bot.guilds:
                    server_remove_date = datetime.now()
                    embed1 = disnake.Embed(title=f"{guild.name} 공지", description=f"```{content}```", color=embedcolor)
                    embed1.set_footer(text=f'To. {ctx.author.display_name}\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
                    try:
                        chan = guild.get_channel(공지채널_id)
                        if chan and chan.permissions_for(guild.me).send_messages:
                            await chan.send(embed=embed1)
                    except Exception as e:
                        print(f"Error sending message to {guild.name}: {e}")  # 예외 로그 추가
            else:
                embed = disnake.Embed(title="오류", description="공지채널이 없습니다.\n공지채널을 설정해주세요.")
                await ctx.send(embed=embed)  # 오류 메시지 전송

            embed = disnake.Embed(title="공지 업로드 완료!", color=embedsuccess)
            await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="추방", description="유저를 추방합니다. [관리자전용]")
async def kick(ctx, user: disnake.Member = commands.Param(name="유저"), reason: str = commands.Param(name="사유", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "추방")
    if ctx.author.guild_permissions.kick_members:
        try:
            await ctx.guild.kick(user)
        except:
            embed = disnake.Embed(title=f"{user.name}를 추방하기엔 권한이 부족해요...", color=embederrorcolor)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(title="✅추방을 완료했어요", color=embedsuccess)
            embed.add_field(name="대상", value=f"{user.mention}")
            embed.add_field(name="사유", value=f"{reason}", inline=False)
            await ctx.send(embed=embed)
            db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
            if not os.path.exists(db_path):
                await database_create(ctx)
            aiodb = await aiosqlite.connect(db_path)
            aiocursor = await aiodb.execute("select * from 설정 order by 공지채널 desc")
            dat = await aiocursor.fetchone()
            await aiocursor.close()
            aiocursor = await aiodb.execute("SELECT 처벌로그 FROM 설정")
            설정_result = await aiocursor.fetchone()
            await aiocursor.close()
            if 설정_result:
                경고채널_id = 설정_result[0]
                경고채널 = bot.get_channel(경고채널_id)
                if 경고채널:
                    embed = disnake.Embed(title="추방", color=embederrorcolor)
                    embed.add_field(name="관리자", value=f"{ctx.author.mention}")
                    embed.add_field(name="대상", value=f"{user.mention}")
                    embed.add_field(name="사유", value=f"{reason}", inline=False)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("경고채널을 찾을 수 없습니다.")
                    embed
            else:
                await ctx.send("경고채널이 설정되지 않았습니다.")
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="차단", description="유저를 차단합니다. [관리자전용]")
async def ban(ctx, user: disnake.Member = commands.Param(description="유저"), reason: str = commands.Param(name="사유", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "차단")
    if ctx.author.guild_permissions.ban_members:
        try:
            await ctx.guild.ban(user)
        except:
            embed = disnake.Embed(title=f"{user.name}를 차단하기엔 권한이 부족해요...", color=embederrorcolor)
            await ctx.send(embed=embed, ephemeral=True)
        else:
            embed = disnake.Embed(title="차단", color=embederrorcolor)
            embed.add_field(name="관리자", value=f"{ctx.author.mention}")
            embed.add_field(name="대상", value=f"{user.mention}")
            embed.add_field(name="사유", value=f"{reason}", inline=False)
            await ctx.send(embed=embed)
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="경고확인", description="보유중인 경고를 확인합니다.")
async def warning_check(ctx, user: disnake.Member = commands.Param(name="유저", default=None)):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "경고확인")
    max_warning = 10
    if user is None:
        user = ctx.author
    dat, accumulatewarn = await getwarn(ctx, user)
    
    if not dat:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="확인된 경고가 없습니다.", value="")
        await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(title=f"{user.name}님의 경고 리스트", color=embedcolor)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name=f"누적경고 : {accumulatewarn} / {max_warning}", value="", inline=False)
        for i in dat:
            embed.add_field(name=f"경고 #{i[0]}", value=f"경고수: {i[3]}\n사유: {i[4]}", inline=False)
        await ctx.send(embed=embed)

@bot.slash_command(name="경고", description="유저에게 경고를 지급합니다. [관리자전용]")
async def warning(ctx, user: disnake.Member, warn_num: int = None, reason: str = None):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "경고")
    max_warning = 10
    if ctx.author.guild_permissions.manage_messages:
        if warn_num is None:
            warn_num = "1"
        if reason is None:
            reason = "없음"
        new_id, accumulatewarn, 설정_result = await addwarn(ctx, user, warn_num, reason)
        if 설정_result:
            경고채널_id = 설정_result[0]
            경고채널 = bot.get_channel(경고채널_id)
            if 경고채널:
                embed = disnake.Embed(title=f"#{new_id} - 경고", color=embederrorcolor)
                embed.add_field(name="관리자", value=ctx.author.mention, inline=False)
                embed.add_field(name="대상", value=user.mention, inline=False)
                embed.add_field(name="사유", value=reason, inline=False)
                embed.add_field(name="누적 경고", value=f"{accumulatewarn} / {max_warning} (+ {warn_num})", inline=False)
                await 경고채널.send(embed=embed)
            else:
                await ctx.send("경고채널을 찾을 수 없습니다.")
        else:
            await ctx.send("경고채널이 설정되지 않았습니다.")
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="경고취소", description="지급한 경고를 취소합니다. [관리자전용]")
async def warning_cancel(ctx, warn_id: int, reason: str = None):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "경고취소")
    if ctx.author.guild_permissions.manage_messages:
        if reason is None:
            reason = "없음"
        warn_id = await removewarn(ctx, warn_id)
        if warn_id is None:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="이미 취소되었거나 없는 경고입니다.", value="")
            await ctx.send(embed=embed)
        else:
            await aiocursor.execute("DELETE FROM 경고 WHERE 아이디 = ?", (warn_id,))
            await aiodb.commit()  # 변경 사항을 데이터베이스에 확정합니다.
            embed = disnake.Embed(color=embedsuccess)
            embed.add_field(name=f"경고 #{warn_id}(이)가 취소되었습니다.", value="")
            embed.add_field(name="사유", value=reason, inline=False)
            await ctx.send(embed=embed)
            aiocursor = await aiodb.execute("SELECT 처벌로그 FROM 설정")
            set_result = await aiocursor.fetchone()
            await aiocursor.close()
            if set_result:
                warnlog_id = set_result[0]
                warnlog = bot.get_channel(warnlog_id)
                if warnlog:
                    embed = disnake.Embed(title=f"#{warn_id} - 경고 취소", color=embedwarning)
                    embed.add_field(name="관리자", value=ctx.author.mention, inline=False)
                    embed.add_field(name="사유", value=reason, inline=False)
                    await warnlog.send(embed=embed)
                else:
                    await ctx.send("경고채널을 찾을 수 없습니다.")
            else:
                await ctx.send("경고채널이 설정되지 않았습니다.")
        await aiocursor.close()
    else:
        embed=disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="문의", description="개발자에게 문의를 보냅니다.")
async def inquire(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "문의")
    embed = disnake.Embed(color=embederrorcolor)
    embed.add_field(name="❌ 오류", value=f"{ctx.author.mention}, 문의는 봇 DM으로 부탁드립니다!")
    await ctx.send(embed=embed)

@bot.slash_command(name="문의답장", description="유저에게 답변을 보냅니다. [개발자전용]")
async def inquire_answer(ctx, member: str, message: str):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "문의답장")

    # 멘션 형식이나 ID에서 ID 추출
    try:
        if member.startswith('<@') and member.endswith('>'):
            member_id = int(member.replace('<@', '').replace('>', '').replace('!', ''))
        else:
            member_id = int(member)  # ID 형식일 경우

    except ValueError:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="올바른 멘션 형식이나 ID가 아닙니다.")
        await ctx.send(embed=embed)
        return

    # 개발자 ID 확인
    if ctx.author.id != developer:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="이 명령어는 개발자만 사용할 수 있습니다.")
        await ctx.send(embed=embed)
        return
    
    # User 객체 생성
    try:
        user = await bot.fetch_user(member_id)  # 유저 정보 가져오기

        await user.send(f"{ctx.author.mention} : {message}")  # DM 전송
        embed = disnake.Embed(title="✅ 전송완료", color=embedcolor)
        embed.add_field(name="대상자", value=f"{user.mention}")
        embed.add_field(name="답장 내용", value=f"{message}")
        await ctx.send(embed=embed)

    except disnake.Forbidden:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value=f"{user.mention}님에게 메시지를 보낼 수 없습니다. DM을 허용하지 않았습니다.")
        await ctx.send(embed=embed)
    except disnake.HTTPException:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="메시지 전송 중 오류가 발생했습니다.")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value=f"오류: {str(e)}")
        await ctx.send(embed=embed)

@bot.slash_command(name="dm_on", description="레벨업 DM 수신을 활성화합니다.")
async def dm_on(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "dm_on")
    db_path = os.path.join('system_database', 'economy.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    async with economy_aiodb.cursor() as aiocursor:
        await aiocursor.execute("SELECT dm_on_off FROM user WHERE id=?", (ctx.author.id,))
        dbdata = await aiocursor.fetchone()

        if dbdata is not None:
            if int(dbdata[0]) == 1:  # 현재 DM 수신이 비활성화된 경우
                await aiocursor.execute("UPDATE user SET dm_on_off=? WHERE id=?", (0, ctx.author.id))
                await economy_aiodb.commit()
                embed = disnake.Embed(color=embedsuccess)
                embed.add_field(name="✅ DM 수신 활성화", value="이제 DM을 수신합니다.")
            else:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이미 DM 수신이 활성화되어 있습니다.")
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="가입이 되어있지 않습니다.")
    
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="dm_off", description="레벨업 DM 수신을 비활성화합니다.")
async def dm_off(ctx):
    if not await check_permissions(ctx):
        return
    await command_use_log(ctx, "dm_off")
    db_path = os.path.join('system_database', 'economy.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    async with economy_aiodb.cursor() as aiocursor:
        await aiocursor.execute("SELECT dm_on_off FROM user WHERE id=?", (ctx.author.id,))
        dbdata = await aiocursor.fetchone()

        if dbdata is not None:
            if int(dbdata[0]) == 0:  # 현재 DM 수신이 활성화된 경우
                await aiocursor.execute("UPDATE user SET dm_on_off=? WHERE id=?", (1, ctx.author.id))
                await economy_aiodb.commit()
                embed = disnake.Embed(color=embedsuccess)
                embed.add_field(name="✅ DM 수신 비활성화", value="이제 DM을 수신하지 않습니다.")
            else:
                embed = disnake.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이미 DM 수신이 비활성화되어 있습니다.")
        else:
            embed = disnake.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="가입이 되어있지 않습니다.")
    
        await ctx.send(embed=embed, ephemeral=True)

@bot.slash_command(name="수동추첨", description="로또를 자동으로 추첨합니다.")
async def manual_lottery_draw(interaction: disnake.ApplicationCommandInteraction):
    # 개발자 ID 확인
    if interaction.author.id != developer:
        embed = disnake.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="이 명령어는 개발자만 사용할 수 있습니다.")
        await interaction.send(embed=embed)
        return
    
    await command_use_log(interaction, "수동추첨")
    # 자동으로 번호 생성
    winning_numbers = random.sample(range(1, 46), 6)
    bonus_number = random.choice([num for num in range(1, 46) if num not in winning_numbers])  # 보너스 번호
    winning_numbers_str = ','.join(map(str, sorted(winning_numbers)))

    # 당첨자 확인
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT user_id, numbers FROM lottery') as cursor:
            winners = await cursor.fetchall()

    # 등수별 당첨자 수 초기화
    prize_counts = {
        "1등": 0,
        "2등": 0,
        "3등": 0,
        "4등": 0,
        "5등": 0,
    }

    embed = disnake.Embed(title="로또 자동 추첨 결과 (수동)", color=0x00ff00)
    embed.add_field(name="당첨 번호", value=f"{winning_numbers_str} (보너스: {bonus_number})", inline=False)

    for winner in winners:
        user_id = winner[0]
        matched_numbers = len(set(winning_numbers) & set(map(int, winner[1].split(','))))
        
        # 당첨자 수 업데이트
        if matched_numbers == 6:
            prize_counts["1등"] += 1
            rank = "1등"
        elif matched_numbers == 5 and bonus_number in map(int, winner[1].split(',')):
            prize_counts["2등"] += 1
            rank = "2등"
        elif matched_numbers == 5:
            prize_counts["3등"] += 1
            rank = "3등"
        elif matched_numbers == 4:
            prize_counts["4등"] += 1
            rank = "4등"
        elif matched_numbers == 3:
            prize_counts["5등"] += 1
            rank = "5등"
        else:
            continue  # 당첨되지 않은 경우

        # DM 전송
        prize_amount = 0
        if rank == "1등":
            prize_amount = 3000000000
        elif rank == "2등":
            prize_amount = 1500000000
        elif rank == "3등":
            prize_amount = 100000000
        elif rank == "4등":
            prize_amount = 10000000
        elif rank == "5등":
            prize_amount = 1000000
        
        if prize_amount > 0:
            user = await bot.fetch_user(user_id)
            if user:
                embed = disnake.Embed(title="🎉 축하합니다!", description=f"당신의 로또 번호가 당첨되었습니다!", color=0x00ff00)
                embed.add_field(name="등수", value=rank, inline=False)  # 올바른 등수 표시
                embed.add_field(name="상금", value=f"{prize_amount:,}원", inline=False)
                await user.send(embed=embed)

    # 등수별 당첨자 수 추가
    embed.add_field(name="당첨자 수", value=f"1등: {prize_counts['1등']}명\n2등: {prize_counts['2등']}명\n3등: {prize_counts['3등']}명\n4등: {prize_counts['4등']}명\n5등: {prize_counts['5등']}명", inline=False)

    # 특정 채널에 결과 전송
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)

    # 로또 데이터 삭제
    async with aiosqlite.connect(db_path) as db:
        await db.execute('DELETE FROM lottery')
        await db.commit()

    await interaction.send("추첨 결과가 지정된 채널에 전송되었으며, 로또 데이터가 삭제되었습니다.")
##################################################################################################
# 처리된 멤버를 추적하기 위한 집합
processed_members = set()

@bot.event
async def on_member_join(member):
    # 이미 처리된 멤버인지 확인
    if member.id in processed_members:
        return  # 이미 처리된 멤버는 무시

    # 처리된 멤버 목록에 추가
    processed_members.add(member.id)

    # 데이터베이스 연결 및 비동기 커서 생성
    await database_create(member)
    db_path = os.path.join(os.getcwd(), "database", f"{member.guild.id}.db")
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.cursor()  # 비동기 커서 생성
    try:
        # 설정 테이블에서 입장 로그 채널 아이디 가져오기
        await aiocursor.execute("SELECT 입장로그 FROM 설정")
        result = await aiocursor.fetchone()
        if result is not None:
            channel_id = result[0]
            # 채널 아이디에 해당하는 채널에 입장 로그 보내기
            channel = bot.get_channel(channel_id)
            if channel is not None:
                embedcolor = 0x00FF00  # 임베드 색상 설정
                embed = disnake.Embed(title="입장로그", color=embedcolor)
                embed.add_field(name="유저", value=f"{member.mention} ({member.name})")
                embed.set_thumbnail(url=member.display_avatar.url)
                server_join_date = datetime.now()  # datetime 클래스를 직접 사용
                account_creation_date = member.created_at
                embed.add_field(name="서버입장일", value=server_join_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                embed.add_field(name="계정생성일", value=account_creation_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                await channel.send(embed=embed)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    finally:
        # 데이터베이스 연결 종료
        await aiocursor.close()
        await aiodb.close()

@bot.event
async def on_member_remove(member):
    # 데이터베이스 연결 및 비동기 커서 생성
    await database_create(member)
    db_path = os.path.join(os.getcwd(), "database", f"{member.guild.id}.db")
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.cursor()  # 비동기 커서 생성
    try:
        await aiocursor.execute("SELECT 퇴장로그 FROM 설정")
        result = await aiocursor.fetchone()
        if result is not None:
            channel_id = result[0]
            channel = bot.get_channel(channel_id)
            if channel is not None:
                embedcolor = 0x00FF00
                embed = disnake.Embed(title="퇴장로그", color=embedcolor)
                embed.add_field(name="유저", value=f"{member.mention} ({member.name})")
                server_remove_date = datetime.now()
                embed.add_field(name="서버퇴장일", value=server_remove_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                await channel.send(embed=embed)
    finally:
        # 데이터베이스 연결 종료
        await aiocursor.close()
        await aiodb.close()

async def check_user_in_db(user_id):
    # 데이터베이스 쿼리 로직
    db_path = os.path.join('system_database', 'economy.db')
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT * FROM user WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

@bot.event
async def on_message(message):
    # 봇이 보낸 메시지는 무시
    if message.author == bot.user or message.author.bot:
        return

    user_id = str(message.author.id)

    # 데이터베이스에서 사용자 데이터 확인
    user_exists = await check_user_in_db(user_id)

    if user_exists:
        await add_exp(user_id, 5)

    # DM 채널에서의 처리
    if isinstance(message.channel, disnake.DMChannel):
        await handle_dm_message(message)

async def handle_dm_message(message):
    user = f"{message.author.display_name}({message.author.name})"
    avatar_url = message.author.avatar.url if message.author.avatar else None

    # 데이터베이스 연결 및 TOS 확인
    db_path = os.path.join('system_database', 'economy.db')
    async with aiosqlite.connect(db_path) as economy_aiodb:
        async with economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (message.author.id,)) as aiocursor:
            dbdata = await aiocursor.fetchone()

    if dbdata is not None and int(dbdata[0]) == 1:
        await send_error_response(message)
        return

    await message.add_reaction("✅")
    print("문의가 접수되었습니다.")
    
    # 임베드 메시지 생성
    dm_embed = disnake.Embed(title="새로운 문의", color=embedcolor)
    dm_embed.add_field(name="사용자", value=user, inline=False)
    dm_embed.add_field(name="아이디", value=message.author.id, inline=False)
    dm_embed.add_field(name="내용", value=str(message.content), inline=False)
    if avatar_url:
        dm_embed.set_thumbnail(url=avatar_url)

    # 특정 채널로 전송
    await send_to_support_channel(dm_embed)

    # 첨부 파일 처리
    await handle_attachments(message)

async def send_error_response(message):
    try:
        await message.add_reaction("❌")
    except Exception as e:
        print(f"이모지 반응 중 오류 발생: {e}")

    embed = disnake.Embed(color=embederrorcolor)
    embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.\n@stone6718 DM으로 문의주세요.")
    await message.channel.send(embed=embed)

async def send_to_support_channel(embed):
    channel_id = int(sec.support_ch_id)
    channel = bot.get_channel(channel_id)

    if channel is None:
        print(f"채널 ID {channel_id}을(를) 찾을 수 없습니다.")
        return

    try:
        await channel.send(embed=embed)
        print(f"메시지가 채널 ID {channel_id}로 전송되었습니다.")
    except Exception as e:
        print(f"메시지를 채널로 전송하는 중 오류 발생: {e}")

async def handle_attachments(message):
    if message.attachments:
        for attachment in message.attachments:
            try:
                # 파일 다운로드 및 전송
                file = await attachment.to_file()
                await send_to_support_channel(file=file)
                print(f"파일 {attachment.filename}이(가) 채널 ID {sec.support_ch_id}로 전송되었습니다.")
            except Exception as e:
                print(f"파일을 채널로 전송하는 중 오류 발생: {e}")

def get_uptime():
    """업타임을 계산하는 함수."""
    now = datetime.now()
    uptime = now - start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}시간 {minutes}분 {seconds}초"

@bot.event
async def on_ready():
    print("\n봇 온라인!")
    print(f'{bot.user.name}')
    change_status.start()
    koreabots.start()

@bot.event
async def on_guild_join(guild):
    await database_create_server_join(guild.id)
    print(f'새로운 서버에 입장했습니다: {guild.name} (ID: {guild.id})')

@bot.event
async def on_guild_remove(guild):
    await delete_server_database(guild.id)
    print(f'서버에서 퇴장했습니다: {guild.name} (ID: {guild.id})')

@tasks.loop(seconds=3)
async def change_status():
    guild_len = len(bot.guilds)
    statuses = [f'음악 재생', '편리한 기능을 제공', f'{guild_len}개의 서버를 관리']
    for i in statuses:
        await bot.change_presence(status=disnake.Status.online, activity=disnake.Game(i))
        await asyncio.sleep(3)

aiodb = {}
economy_aiodb = None

@tasks.loop(seconds=3)
async def koreabots():
    url = f"https://koreanbots.dev/api/v2/bots/{bot.user.id}/stats"
    headers = {
        "Authorization": sec.koreanbots_api_key,
        "Content-Type": "application/json"
    }
    body = {
        "servers": len(bot.guilds),
        "shards": 1,
    }

    followup = requests.post(url=url, data=json.dumps(body), headers=headers)
    data = followup.json()

@tasks.loop()
async def periodic_price_update():
    while True:
        await update_stock_prices()
        await update_coin_prices()
        await asyncio.sleep(20)

periodic_price_update.start()

# 매일 09시에 출석 체크 상태를 초기화하는 작업
@tasks.loop(seconds=1)  # 1초마다 실행
async def reset_check_in_status():
    now = datetime.now(pytz.timezone('Asia/Seoul'))  # KST로 현재 시각 가져오기
    if now.hour == 9 and now.minute == 0 and now.second == 0:  # 09시 00분 00초에 실행
        db_path = os.path.join('system_database', 'economy.db')
        
        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.cursor()
            await cursor.execute("UPDATE user SET checkin = 0")
            await conn.commit()
        
        print("모든 사용자의 체크인 상태가 초기화되었습니다.")

reset_check_in_status.start()

db_path = os.path.join('system_database', 'lotto.db')
channel_id = 1300246995956404224  # 특정 채널 ID

@tasks.loop(seconds=1)  # 매 1초마다 체크
async def lottery_draw():
    tz = pytz.timezone('Asia/Seoul')  # KST 설정
    now = datetime.now(tz)  # 현재 KST 시간 가져오기
    if now.weekday() == 5 and now.hour == 21 and now.minute == 0 and now.second == 0:  # 매주 토요일 21시 0분 0초
        await draw_lottery()

lottery_draw.start()

async def draw_lottery():
    async with aiosqlite.connect(db_path) as db:
        # 당첨 번호 생성
        winning_numbers = random.sample(range(1, 46), 6)
        bonus_number = random.choice([num for num in range(1, 46) if num not in winning_numbers])  # 보너스 번호
        winning_numbers_str = ','.join(map(str, sorted(winning_numbers)))
        
        # 당첨자 확인
        async with db.execute('SELECT user_id, numbers FROM lottery') as cursor:
            winners = await cursor.fetchall()

        # 등수별 당첨자 수 초기화
        prize_counts = {
            "1등": 0,
            "2등": 0,
            "3등": 0,
            "4등": 0,
            "5등": 0,
        }

        # 임베드 메시지 생성
        # 현재 시간을 KST로 가져오기
        kst_now = datetime.now() + timedelta(hours=9)  # UTC+9

        # 월과 주차 계산
        month = kst_now.month
        week_of_month = (kst_now.day - 1) // 7 + 1
        embed = disnake.Embed(title=f"로또 추첨 결과 ({month}/{week_of_month}주)", color=0x00ff00)
        embed.add_field(name="당첨 번호", value=f"{winning_numbers_str} (보너스: {bonus_number})", inline=False)
        
        if winners:
            for winner in winners:
                user_id = winner[0]
                # 당첨금 지급
                matched_numbers = len(set(winning_numbers) & set(map(int, winner[1].split(','))))
                prize_amount = 0

                if matched_numbers == 6:
                    prize_amount = 3000000000
                    prize_counts["1등"] += 1
                elif matched_numbers == 5 and bonus_number in map(int, winner[1].split(',')):
                    prize_amount = 1500000000
                    prize_counts["2등"] += 1
                elif matched_numbers == 5:
                    prize_amount = 100000000
                    prize_counts["3등"] += 1
                elif matched_numbers == 4:
                    prize_amount = 10000000
                    prize_counts["4등"] += 1
                elif matched_numbers == 3:
                    prize_amount = 1000000
                    prize_counts["5등"] += 1

                if prize_amount > 0:
                    await addmoney(user_id, prize_amount)
                    embed.add_field(name=f"{user_id}님", value=f"{prize_amount:,}원이 지급되었습니다.", inline=False)

                    # 당첨자에게 DM 전송
                    user = await bot.fetch_user(user_id)
                    if user:
                        await user.send(f"축하합니다! 당신의 로또 번호가 당첨되었습니다!\n당첨 금액: {prize_amount}원")

            # 등수별 당첨자 수 추가
            embed.add_field(name="당첨자 수", value=f"1등: {prize_counts['1등']}명\n2등: {prize_counts['2등']}명\n3등: {prize_counts['3등']}명\n4등: {prize_counts['4등']}명\n5등: {prize_counts['5등']}명", inline=False)
            print(embed.to_dict())
        else:
            embed.add_field(name="결과", value="당첨자 없음.", inline=False)
            print(embed.to_dict())

        # 특정 채널에 결과 전송
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

        # 로또 데이터 삭제 (테이블 구조 유지)
        await db.execute('DELETE FROM lottery')
        await db.commit()
        print("로또 데이터가 삭제되었습니다.")

@tasks.loop(hours=12)
async def check_expired_members():
    db_path = os.path.join('system_database', 'membership.db')
    economy_aiodb = await aiosqlite.connect(db_path)
    current_date = datetime.now().strftime('%Y/%m/%d')
    
    # 만료된 회원을 비회원으로 변경
    await economy_aiodb.execute("UPDATE user SET class = 0 WHERE class = 1 AND expiration_date < ?", (current_date,))
    await economy_aiodb.commit()
    await economy_aiodb.close()

check_expired_members.start()

limit_level = 1000  # 최대 레벨

def calculate_experience_for_level(current_level):
    if current_level is None:
        current_level = 1  # 기본값 설정
        
    E_0 = 100  # 기본 경험치
    r = 1.5    # 경험치 증가 비율
    k = 50     # 추가 경험치

    n = current_level
    base_experience = math.floor(E_0 * (r ** (n - 1)) + k)
    return base_experience

@tasks.loop(seconds=20)  # 20초마다 실행
async def check_experience():
    db_path = os.path.join('system_database', 'economy.db')
    async with aiosqlite.connect(db_path) as conn:
        async with conn.cursor() as c:
            await c.execute('SELECT id, exp, level, money FROM user')
            rows = await c.fetchall()
            
            updates = []
            messages = []

            for row in rows:
                user_id, current_experience, current_level, current_balance = row
                
                # 기본값 설정
                current_experience = current_experience if current_experience is not None else 0
                current_level = current_level if current_level is not None else 1
                current_balance = current_balance if current_balance is not None else 0

                required_experience = calculate_experience_for_level(current_level)
                new_level = current_level
                
                while current_experience >= required_experience and new_level < limit_level:
                    new_level += 1
                    required_experience = calculate_experience_for_level(new_level)

                adjusted_level = new_level - 1

                if adjusted_level > current_level:
                    updates.append((adjusted_level, user_id))
                    if adjusted_level < limit_level:
                        messages.append((user_id, adjusted_level))
                        
                        # 레벨업 보상 추가
                        reward = adjusted_level * 10000
                        new_balance = current_balance + reward
                        await c.execute('UPDATE user SET money = ? WHERE id = ?', (new_balance, user_id))

            if updates:
                await c.executemany('UPDATE user SET level = ? WHERE id = ?', updates)
            
            await conn.commit()

    for user_id, adjusted_level in messages:
        try:
            user = await bot.fetch_user(user_id)
            dm_setting = await dm_on_off(user)  # DM 설정을 가져옴
            if dm_setting != 1:  # DM 수신이 비활성화된 경우 메시지를 보내지 않음
                if user:
                    channel = await user.create_dm()
                    adjusted_level = adjusted_level * 10000
                    embed = disnake.Embed(
                        title="레벨 업! 🎉",
                        description=f'축하합니다! 레벨이 **{adjusted_level}**로 올랐습니다! 보상으로 **{adjusted_level}원**이 지급되었습니다.',
                        color=0x00ff00
                    )
                    await channel.send(embed=embed)
            else:
                print(f"사용자 {user_id}는 DM 수신이 비활성화되어 있습니다.")
        except disnake.errors.NotFound:
            print(f"사용자를 찾을 수 없습니다: {user_id}")
        except disnake.errors.HTTPException as e:
            print(f"DM을 보낼 수 없습니다: {e}")

check_experience.start()

# 크레딧 부여 스케줄러
scheduled_credits = {}  # 사용자 ID를 키로 하고 (amount) 튜플을 값으로 하는 딕셔너리

async def get_user_class(user_id):
    # 비동기 데이터베이스 연결
    async with connect_db() as conn:
        async with conn.execute("SELECT class FROM user WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    return result[0] if result else None  # 클래스 값 반환

def calculate_credit(user_class):
    # 클래스에 따라 크레딧 계산
    if user_class == 0:
        return 3
    elif user_class == 1:
        return 30
    elif user_class == 2:
        return 60
    return 0  # 기본값

@tasks.loop(seconds=60)  # 1분마다 실행
async def grant_scheduled_credits():
    now = datetime.now(pytz.timezone('Asia/Seoul'))  # 한국 시간으로 현재 시각 가져오기
    if now.hour == 21 and now.minute == 0:  # 21시 00분에 크레딧 부여
        for user_id in list(scheduled_credits.keys()):
            user_class = await get_user_class(user_id)  # 사용자 클래스 가져오기
            if user_class is not None:
                amount = calculate_credit(user_class)  # 크레딧 계산
                await add_user_credit(user_id, amount)
                print(f"{amount} 크레딧이 {user_id}에게 부여되었습니다.")
                # 다음 날 크레딧 부여를 위해 다시 추가
                scheduled_credits[user_id] = (amount)  # 유지

grant_scheduled_credits.start()

# 데이터베이스가 있는 디렉토리
db_directory = './database'  # 실제 경로로 변경하세요

async def startup():
    await bot.start(token, reconnect=True)
    global aiodb
    aiodb = {}
    for guild in bot.guilds:
        db_path = os.path.join(os.getcwd(), "database", f"{guild.id}.db")
        aiodb[guild.id] = await aiosqlite.connect(db_path)
    global economy_aiodb
    if economy_aiodb is None:
        db_path = os.path.join('system_database', 'economy.db')
        economy_aiodb = await aiosqlite.connect(db_path)

async def shutdown():
    for aiodb_instance in aiodb.values():
        await aiodb_instance.close()
    await aiodb.close()
    await economy_aiodb.close()
try:
    (asyncio.get_event_loop()).run_until_complete(startup())
except KeyboardInterrupt:
    (asyncio.get_event_loop()).run_until_complete(shutdown())