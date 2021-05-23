from flask import Flask, render_template, request, session, redirect, url_for
import os
import requests
import config
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import uuid





# 기본 세팅
app = Flask(__name__)
app.config.from_pyfile('config/config.py')

# 키 설절
app.secret_key = app.config['SECRET_KEY']
RIOT_API_KEY = app.config['RIOT_API_KEY']

# DB 설정
my_client = MongoClient(app.config['DB_URL'])
# my_client = MongoClient("mongodb://localhost:27017/")

mydb = my_client['dodgeme'] 

# 로그인 여부 확인
def require_login():
    if "user_info" in session:
        return True
    else:
        return False


@app.route('/community')
def community():
    return render_template('community.html')

# 글작성 페이지
@app.route('/community_write_update/<idx>', methods=['GET'])
def community_write_update(idx):
    if require_login():
        mycol = mydb['community'] 
        col = list(mycol.find({'_id':ObjectId(idx)}))
        return render_template('community_write_update.html', col=col[0])
    else:
        return redirect(url_for('signin_page'))

@app.route('/community_write')
def community_write():
    if require_login():
        return render_template('community_write.html')
    else:
        return redirect(url_for('signin_page'))

# 글저장 
@app.route('/community_create', methods=['POST'])
def community_create():
    mycol = mydb['community'] 
    path = "./static/board-img"
    file_list = os.listdir(path)
    if request.method == 'POST':
        date =  str(datetime.now()).split(' ')
        imgname = ""
        file_flag = True
        f = request.files['board-image']
        for fname in file_list:
            if fname == f.filename:
                imgname = str(uuid.uuid4()) + f.filename
                file_flag = False
        if file_flag:
            imgname = f.filename
        if imgname != "":
            f.save("./static/board-img/"+secure_filename(imgname))
        board_data = {
            "type" : request.form['type'],
            "board-title" : request.form['board-title'],
            "board-contents" : request.form['board-contents'],
            "img-name" : imgname,
            "date" : date[0],
            "writer_info" : session['user_info']
        }
        mycol.insert(board_data)
        return redirect(url_for('community'))

@app.route('/community_delete/<idx>', methods=['GET'])
def community_delete(idx: str):
    mycol = mydb['community'] 
    col = mycol.remove({'_id':ObjectId(idx)})
    return redirect(url_for('community'))

@app.route('/community_update/', methods=['POST'])
def community_update():
    mycol = mydb['community'] 
    path = "./static/board-img"
    file_list = os.listdir(path)
    if request.method == 'POST':
        date =  str(datetime.now()).split(' ')
        imgname = ""
        file_flag = True
        f = request.files['board-image']
        for fname in file_list:
            if fname == f.filename:
                imgname = str(uuid.uuid4()) + f.filename
                file_flag = False
        if file_flag:
            imgname = f.filename
        if imgname != "":
            f.save("./static/board-img/"+secure_filename(imgname))
        idx = request.form['idx']
        mycol.update({'_id':ObjectId(idx)}, {"$set":{"board-title" : request.form['board-title']}})
        mycol.update({'_id':ObjectId(idx)}, {"$set":{"board-contents" : request.form['board-contents']}})
        mycol.update({'_id':ObjectId(idx)}, {"$set":{"img-name" : imgname}})
        mycol.update({'_id':ObjectId(idx)}, {"$set":{"date" : date[0]}})
        mycol.update({'_id':ObjectId(idx)}, {"$set":{"type" : request.form['type']}})
        return redirect(url_for('community'))
    

@app.route('/community_getdata')
def community_getdata():
    mycol = mydb['community']
    community_data = list(mycol.find())
    community_data.reverse()
    
    result = []
    for cd in community_data:
        col = {
            'idx' : str(cd['_id']),
            'type' : str(cd['type']),
            'board-title' : str(cd['board-title']),
            'board-contents' : str(cd['board-contents']),
            'img-name' : str(cd['img-name']),
            'date' : str(cd['date']),
            'writer_info' : cd['writer_info']
        }
        result.append(col)
    
    return {'data' : result}

@app.route('/signup', methods=['POST'])
def signup():
    mycol = mydb['user_info'] 
    login_user_id = request.form['user_id']
    
    idCheck = mycol.find_one({"user_id" : login_user_id})
    if idCheck:
        return {"check" : "이미 사용중인 아이디 입니다."}
    else:
        user_age = request.form['user_birth_year'] + "-" + request.form['user_birth_month'] + "-" +request.form['user_birth_day']
        user_db = {
            "user_id" : login_user_id,
            "user_pw" : request.form['user_pw'],
            "user_name" : request.form['user_name'],
            "user_age" : user_age,
            "user_gender" : request.form['user_gender'],
            "user_email" : request.form['user_email']
        }
        mycol.insert(user_db)
        return render_template('signup_success.html')
    

    
@app.route('/check_id_duplicate', methods=['POST'])
def check_id_duplicate():
    mycol = mydb['user_info'] 
    login_user_id = request.form['user_id']
    
    idCheck = mycol.find_one({"user_id" : login_user_id})
    if idCheck:
        return {"check" : "이미 사용중인 아이디 입니다."}
            
    return {"check" : "ok"}
    

@app.route('/signup_page')
def signup_page():
   return render_template('signup_page.html')

@app.route('/signin_page')
def signin_page():
    return render_template('signin_page.html')

@app.route('/signin', methods=['POST'])
def signin():
    mycol = mydb['user_info'] 
    login_user_id = request.form['user_id']
    login_user_pw = request.form['user_pw']
    for i in mycol.find({'user_id' : login_user_id}):
        if i['user_pw'] == login_user_pw:
            session['user_info'] = [i['user_id'], i['user_name'], i['user_email']]
            return {'result' : 'login_success'}
    return {'result' : 'login_fail'}

@app.route('/logout')
def logout():
    session.pop('user_info', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/champion')
def champion():
    initial = request.args.get("initial")
    url_version = "https://ddragon.leagueoflegends.com/api/versions.json"
    res_version = requests.get(url=url_version).text
    version = ""
    for v in range(2, 15):
        if res_version[v] == '"':
            break
        else:
            version = version + res_version[v]

    url_champ = "http://ddragon.leagueoflegends.com/cdn/{}/data/ko_KR/champion.json".format(version)
    res_champ = requests.get(url=url_champ)
    champ = res_champ.json().get('data')

    # 초성 리스트. 00 ~ 18
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    # 중성 리스트. 00 ~ 20
    JUNGSUNG_LIST = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
    # 종성 리스트. 00 ~ 27 + 1(1개 없음)
    JONGSUNG_LIST = [' ', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

    def korean_spelling(korean_word):
        r_lst = []
        for w in list(korean_word.strip()):
            ## 영어인 경우 구분해서 작성함. 
            if '가'<=w<='힣':
                ## 588개 마다 초성이 바뀜. 
                ch1 = (ord(w) - ord('가'))//588
                ## 중성은 총 28가지 종류
                ch2 = ((ord(w) - ord('가')) - (588*ch1)) // 28
                ch3 = (ord(w) - ord('가')) - (588*ch1) - 28*ch2
                r_lst.append([CHOSUNG_LIST[ch1], JUNGSUNG_LIST[ch2], JONGSUNG_LIST[ch3]])
            else:
                r_lst.append([w])
        return r_lst

    def get_champ_info(param):
        if initial is not None:
            if initial == korean_spelling(param.get("name"))[0][0] :
                res=[
                    param.get('id'),
                    param.get('name'),
                    param.get('image'),
                ]
                return res
        else :
            res=[
                param.get('id'),
                param.get('name'),
                param.get('image'),
            ]
            return res

    champ_arr = []
    for i in champ:
        if get_champ_info(champ[i]) is not None:
            champ_arr.append(get_champ_info(champ[i]))

    champ_arr.sort(key=lambda x:x[1])
    return render_template('champion.html',champ=champ_arr)

@app.route('/champ/detail')
def champDetail():
    champName = request.args.get('name')
    url_version = "https://ddragon.leagueoflegends.com/api/versions.json"
    res_version = requests.get(url=url_version).text
    version = ""
    for v in range(2, 15):
        if res_version[v] == '"':
            break
        else:
            version = version + res_version[v]

    url_champ = "http://ddragon.leagueoflegends.com/cdn/{}/data/ko_KR/champion/{}.json".format(version, champName)
    res_champ = requests.get(url=url_champ)
    champ = res_champ.json().get('data')

    # 챔피언 명
    champNameKR = champ.get(champName).get('name')
    champTitle = champ.get(champName).get('title')
    lore = champ.get(champName).get('lore')

    # 챔피언 스킨 정보
    champSkins = champ.get(champName).get('skins')
    for i in champSkins:
        if i['name'] == 'default':
            i['name'] = '기본'
        i['img'] = "http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{}_{}.jpg".format(champName, i.get('num'))
    

    # 챔피언 이미지
    champImg = "http://ddragon.leagueoflegends.com/cdn/{}/img/champion/".format(version) + champ.get(champName).get('image').get('full')

    # 스킬
    skills = []
    spells = champ.get(champName).get('spells')
    passive = {
        "id": "passive",
        "name": champ.get(champName).get('passive').get('name'),
        "description" : champ.get(champName).get('passive').get('description'),
        "img" : "http://ddragon.leagueoflegends.com/cdn/{}/img/passive/{}".format(version, champ.get(champName).get('passive').get('image').get('full')),
    }
    skills.append(passive)
    for i in spells:
        skill = {
            "id" : i.get('id')[-1],
            "name" : i.get('name'),
            "description" : i.get('description'),
            "img" : "http://ddragon.leagueoflegends.com/cdn/{}/img/spell/{}.png".format(version, i.get('id')),
        }
        skills.append(skill)
    
    print(skills)

    return render_template('detailChamp.html', champ=champ, champImg=champImg, champNameKR=champNameKR, skills=skills, champSkins=champSkins, lore=lore)
    
    
@app.route('/search')
def search():
    url_version = "https://ddragon.leagueoflegends.com/api/versions.json"
    res_version = requests.get(url=url_version).text
    version = ""
    for v in range(2, 15):
        if res_version[v] == '"':
            break
        else:
            version = version + res_version[v]

    sum_name = request.args.get('name')
    
    url = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}".format(sum_name)
    headers = {
        "Origin": "https://developer.riotgames.com",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Riot-Token": RIOT_API_KEY,
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    }
    res = requests.get(url=url,headers=headers)
    encrypted_id = res.json()['id']
    level = res.json()['summonerLevel']
    fix_name = res.json()['name']
    account_id = res.json()['accountId']
    profileIconId = res.json()['profileIconId']
    url_league = "https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/{}".format(encrypted_id)
    res_league = requests.get(url=url_league,headers=headers)
    league_dicts = res_league.json()
    profileIcon = 'http://ddragon.leagueoflegends.com/cdn/{}/img/profileicon/{}.png'.format(version, profileIconId)


    url_mastery = "https://kr.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{}".format(encrypted_id)
    res_mastery = requests.get(url=url_mastery,headers=headers)
    mastery = res_mastery.json()


    url_champ = "http://ddragon.leagueoflegends.com/cdn/{}/data/ko_KR/champion.json".format(version)
    res_champ = requests.get(url=url_champ)
    champ = res_champ.json().get('data')
    
    url_game_id = "https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/{}".format(account_id)
    res_game_id = requests.get(url=url_game_id, headers=headers)
    game_id = res_game_id.json().get('matches')



    last_game_data = []
    for i in range(0, 5):
        last_game_data.append(game_id[i])

    game_que_type = {
        "450" : "칼바람 나락",
        "430" : "일반게임",
        "420" : "솔로랭크",
        "440" : "자유랭크",
        "830" : "봇 입문",
        "840" : "봇 초보",
        "850" : "봇 중급",
        "1020" : "단일챔피언",
        "900" : "URF"
    }
    
    def get_quetype(key):
        keyy = str(key)
        for i in game_que_type:
            if i == keyy:
                return game_que_type.get(keyy)


    #item
    url_item = "http://ddragon.leagueoflegends.com/cdn/{}/data/ko_KR/item.json".format(version)
    res_item = requests.get(url=url_item)
    item = res_item.json().get('data')
    

    #spell
    url_spell = "http://ddragon.leagueoflegends.com/cdn/{}/data/ko_KR/summoner.json".format(version)
    res_spell = requests.get(url=url_spell)
    spell = res_spell.json().get('data')


    def get_item_name(key):
        if key == 0:
            return 'none'
        return item.get(str(key)).get('name')

    def get_item_img(key):
        if key == 0:
            return "empty"
        try:
            img = item.get(str(key)).get('image').get('full')
            return "http://ddragon.leagueoflegends.com/cdn/{}/img/item/".format(version)+img
        except Exception as e:
            print(e)
        

    def get_champ_name(keyy):
        for i in champ:
            if champ.get(i).get('key') == str(keyy):
                return champ.get(i).get('name')
                

    def get_champ_img(key):
        for i in champ:
            if champ.get(i).get('key') == str(key):
                img = champ.get(i).get('image').get('full')
                return "http://ddragon.leagueoflegends.com/cdn/{}/img/champion/".format(version)+img
    

    def get_spell_name(key):
        for i in spell:
            if spell.get(i).get('key') == str(key):
                return spell.get(i).get('name') 

    def get_spell_img(key):
        for i in spell:
            if spell.get(i).get('key') == str(key):
                img = spell.get(i).get('image').get('full')
                return "http://ddragon.leagueoflegends.com/cdn/{}/img/spell/".format(version)+img

    def get_mastery_img(num):
        if num == 1:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/d/d8/Champion_Mastery_Level_1_Flair.png/revision/latest/scale-to-width-down/50?cb=20150312005229"
        elif num == 2:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/4/4d/Champion_Mastery_Level_2_Flair.png/revision/latest/scale-to-width-down/50?cb=20150312005244"
        elif num == 3:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/e/e5/Champion_Mastery_Level_3_Flair.png/revision/latest/scale-to-width-down/50?cb=20150312005319"
        elif num == 4:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/b/b6/Champion_Mastery_Level_4_Flair.png/revision/latest/scale-to-width-down/50?cb=20200113041829"
        elif num == 5:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/9/96/Champion_Mastery_Level_5_Flair.png/revision/latest/scale-to-width-down/50?cb=20200113041512"
        elif num == 6:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/b/be/Champion_Mastery_Level_6_Flair.png/revision/latest/scale-to-width-down/50?cb=20200113041636"
        elif num == 7:
            return "https://vignette.wikia.nocookie.net/leagueoflegends/images/7/7a/Champion_Mastery_Level_7_Flair.png/revision/latest/scale-to-width-down/50?cb=20200113041615"
        
    



    def get_mastery_info(mastery):
        res=[
            mastery.get('championId'),
            mastery.get('championLevel'),
            mastery.get('championPoints'),
        ]
        return res
    mastery_arr = []
    for i in range(0, 3):
        mastery_arr.append(get_mastery_info(mastery[i]))
    

    def fix_mastery_name(master):
        result = []
        for i in mastery_arr:
            fix = [
                get_champ_img(i[0]),
                get_mastery_img(i[1]),
                i[2]
            ]
            result.append(fix)
        return result

    most_pick = fix_mastery_name(mastery_arr)
   

    def get_league_info(league_dict):
        res = [
            league_dict.get('queueType'),
            league_dict.get('tier'),
            league_dict.get('rank'),
            league_dict.get('wins'),
            league_dict.get('losses'),
            league_dict.get('leaguePoints')
        ]
        return res

    rank_info = []
    for league_dict in league_dicts:
        rank_info.append(get_league_info(league_dict))
    length = len(rank_info)



    def get_tear_img (r):
        rank_type = []
        if r[1] == 'IRON':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/0/03/Season_2019_-_Iron_1.png/revision/latest/scale-to-width-down/130?cb=20181229234926')
        elif r[1] == 'BRONZE':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/f/f4/Season_2019_-_Bronze_1.png/revision/latest/scale-to-width-down/130?cb=20181229234910')
        elif r[1] == 'SILVER':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/7/70/Season_2019_-_Silver_1.png/revision/latest/scale-to-width-down/130?cb=20181229234936')
        elif r[1] == 'GOLD':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/9/96/Season_2019_-_Gold_1.png/revision/latest/scale-to-width-down/130?cb=20181229234920')
        elif r[1] == 'PLATINUM':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/7/74/Season_2019_-_Platinum_1.png/revision/latest/scale-to-width-down/130?cb=20181229234932')
        elif r[1] == 'DIAMOND':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/9/91/Season_2019_-_Diamond_1.png/revision/latest/scale-to-width-down/130?cb=20181229234917')
        elif r[1] == 'MASTER':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/1/11/Season_2019_-_Master_1.png/revision/latest/scale-to-width-down/130?cb=20181229234929')
        elif r[1] == 'GRANDMASTER':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/7/76/Season_2019_-_Grandmaster_1.png/revision/latest/scale-to-width-down/130?cb=20181229234923')
        elif r[1] == 'CHALLENGER':
            rank_type.append('https://vignette.wikia.nocookie.net/leagueoflegends/images/5/5f/Season_2019_-_Challenger_1.png/revision/latest/scale-to-width-down/130?cb=20181229234913')
        return rank_type[0]

                

    rank_data = []
    if length != 0:
        for r in rank_info:
            if r[0] == 'RANKED_FLEX_SR':
                solo_rank = ['자유랭크']
                solo_rank.append(get_tear_img(r))
                solo_rank.append(r[1] + r[2])
                solo_rank.append(r[3])
                solo_rank.append(r[4])
                solo_rank.append(r[5])
                rank_data.append(solo_rank)
            elif r[0] == 'RANKED_SOLO_5x5':
                free_rank = ['솔로랭크']
                free_rank.append(get_tear_img(r))
                free_rank.append(r[1] + r[2])
                free_rank.append(r[3])
                free_rank.append(r[4])
                free_rank.append(r[5])
                rank_data.append(free_rank)
                


    game_data_list = []
    for g in last_game_data:
        url_game_data = "https://kr.api.riotgames.com/lol/match/v4/matches/{}".format(g.get('gameId'))
        res_game_data = requests.get(url=url_game_data, headers=headers)
        game_data = res_game_data.json()
        game_data_list.append(game_data)


    game_info = []

    for i in game_data_list:
        player_data_list = []
        win = []
        lose = []
        quetype = get_quetype(i.get('queueId'))
        for j in range(0, 10):
            teamId = i.get('participants')[j].get('teamId')
            champName = get_champ_img(i.get('participants')[j].get('championId'))
            spell1 = get_spell_img(i.get('participants')[j].get('spell1Id'))
            spell2 = get_spell_img(i.get('participants')[j].get('spell2Id'))
            itemList = [
                get_item_img(i.get('participants')[j].get('stats').get('item0')),
                get_item_img(i.get('participants')[j].get('stats').get('item1')),
                get_item_img(i.get('participants')[j].get('stats').get('item2')),
                get_item_img(i.get('participants')[j].get('stats').get('item3')),
                get_item_img(i.get('participants')[j].get('stats').get('item4')),
                get_item_img(i.get('participants')[j].get('stats').get('item5')),
                get_item_img(i.get('participants')[j].get('stats').get('item6')),
            ]
            nickname = i.get('participantIdentities')[j].get('player').get('summonerName')
            if nickname == fix_name:
                if i.get('participants')[j].get('stats').get('win'):
                    victory = "WIN"
                else :
                    victory = "LOSE"
            play_info = {
                "name" : nickname,
                "teamId" : teamId,
                "champ" : champName,
                "spell1" : spell1,
                "spell2" : spell2,
                "item" : itemList
            }
            player_data_list.append(play_info)
        if i.get('participants')[0].get('stats').get('win'):
            
            for t in range(0, 10):
                if t < 5:
                    win.append(player_data_list[t])
                else:
                    lose.append(player_data_list[t])
        else:
            for t in range(0, 10):
                if t > 4:
                    win.append(player_data_list[t])
                else:
                    lose.append(player_data_list[t])

        hangame = {
            "victory":victory,
            "type" : quetype,
            "winteam" : win,
            "loseteam" : lose,
        }
        game_info.append(hangame)
    

    ingame_info = []
    try:
        url_ingame = "https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/{}".format(encrypted_id)
        res_ingame = requests.get(url=url_ingame, headers=headers)
        ingame = res_ingame.json()
        ingame_user = ingame.get('participants')
        user_data_list = []
        if ingame_user == None:
            ingame_info.append('nogame')
        else:
            gameQueueConfigId = ingame.get('gameQueueConfigId')
            ingame_info.append(get_quetype(gameQueueConfigId))
            blueteam =[]
            purpleteam = []
            for user in ingame_user:
                user_teamId = user.get('teamId')
                user_champ = get_champ_img(user.get('championId'))
                user_spell1 = get_spell_img(user.get('spell1Id'))
                user_spell2 = get_spell_img(user.get('spell2Id'))
                user_name = user.get('summonerName')
                user_data = {
                    "name" : user_name,
                    "champ" : user_champ,
                    "spell1" : user_spell1,
                    "spell2" : user_spell2,
                    "team" : user_teamId
                }
                user_data_list.append(user_data)
            for team in user_data_list:
                if team.get('team') == 100:
                    blueteam.append(team)
                else:
                    purpleteam.append(team)
            ingame_info.append(blueteam)
            ingame_info.append(purpleteam)

    except Exception as e:
        print(e)


    return render_template('search.html',sum_name=sum_name, length=length, mostpick=most_pick, last_game_data=last_game_data, game_info=game_info, rank_data=rank_data, profileIcon=profileIcon, ingame_info=ingame_info, level=level)
