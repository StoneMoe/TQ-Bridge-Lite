#!/usr/bin/env python
# coding:utf-8
from flask import Flask, request, Response
import json
import os
import time
import random
import traceback
import urllib2
import re
import urllib

app = Flask(__name__)
app.debug = True

# Config

# bot account
tgbot_nickname = u"xxx bot"
tgbot_username = "xxx_bot"
tgbot_master_id = 0  # 私聊中也可以使用 /chatid 获得id
tgbot_token = "your token"

qqbot_nickname = u"xxx_bot"
qqbot_qq = "0000"

# Webhook Url
tgbot_url = "/%s" % tgbot_token
qqbot_url = "/bot"
# Telegram QQ Group sync rule
redirect_rules = {"QQGroupID": "TelegramGroupID",  # 用 /chatid 可以在QQ群和TG群获取id
                  # "1102815163": 000000000,  # A Certain Scientific QQGroup
                  # "2129551120": -14509134,  # ACG Hackers
                  # "639555831": -6568141 # Typcn Group #1
}


def tgbot_main(jraw):
    j = json.loads(jraw)

    message = j["message"]
    chat = message["chat"]
    chatType = chat["type"]
    user = message["from"]

    # fix crash when info is not exist
    user.setdefault("first_name", "")
    user.setdefault("last_name", "")
    user.setdefault("username", "")

    chat.setdefault("first_name", "")
    chat.setdefault("last_name", "")
    chat.setdefault("username", "")
    chat.setdefault("title", "")

    message.setdefault("caption", "")

    IS_PRIV = False
    IS_GROUP = False
    IS_SGROUP = False
    IS_CH = False

    # Perpare log
    if chatType == "private":
        log_prefix = u"[私聊] %s %s(@%s): " % (user["first_name"], user["last_name"], user["username"])
        IS_PRIV = True
    elif chatType == "group":
        log_prefix = u"[群消息] %s %s(@%s)|%s: " % (user["first_name"], user["last_name"], user["username"], chat["title"])
        IS_GROUP = True
    elif chatType == "supergroup":
        log_prefix = u"[超级群] %s %s(@%s)|%s: " % (user["first_name"], user["last_name"], user["username"], chat["title"])
        IS_SGROUP = True
    elif chatType == "channel":
        log_prefix = u"[频道] %s(%s): " % (chat["title"], chat["username"])
        IS_CH = True
    else:
        log("tgbot", "err", u"无法解析会话类型")
        raise Exception("Cannot parse chatType")

    # Test msg type
    if "text" in message:
        text = message["text"]
        log("tgbot", "msg", log_prefix + text)

        IS_SPECIAL = False
        if ("@" + tgbot_username) in text:
            IS_SPECIAL = True

        text = text.replace("@" + tgbot_username, "")

        # Test command
        if (text[0] == "/" and IS_PRIV) or (text[0] == "/" and IS_SPECIAL):
            return tgbot_gen_responseText(chat, tgbot_processCmd(text[1:], chat, user))
        elif IS_SPECIAL or IS_PRIV:
            return ""
        else:
            for qqgid, tggid in redirect_rules.iteritems():
                if tggid == chat["id"]:
                    qqbot_api_sendGroupText(qqgid, "TG|%s: %s" % (user["username"], text))
            return ""
    elif "voice" in message:
        log("tgbot", "msg", log_prefix + "[Voice]")
        return ""
    elif "document" in message:
        log("tgbot", "msg", log_prefix + "[Document]")
        return ""
    elif "location" in message:
        log("tgbot", "msg", log_prefix + "[Location]")
        return ""
    elif "audio" in message:
        log("tgbot", "msg", log_prefix + "[Audio]")
        return ""
    elif "video" in message:
        log("tgbot", "msg", log_prefix + "[Video](%s)" % message["caption"])
        return ""
    elif "photo" in message:
        log("tgbot", "msg", log_prefix + "[Photo](%s)" % message["caption"])
        return ""
    elif "contact" in message:
        log("tgbot", "msg", log_prefix + "[Contact]")
        return ""
    elif "sticker" in message:
        log("tgbot", "msg", log_prefix + "[Sticker]")
        return ""
    elif "new_chat_photo" in message:
        log("tgbot", "info", log_prefix + u"设置了新的会话头像")
        return ""
    elif "new_chat_participant" in message:
        p = message["new_chat_participant"]
        p.setdefault("first_name", "")
        p.setdefault("last_name", "")
        p.setdefault("username", "")
        log("tgbot", "info", log_prefix + u"邀请 %s %s(@%s) 加入了该会话" % (p["first_name"], p["last_name"], p["username"]))
        return ""
    elif "left_chat_participant" in message:
        p = message["left_chat_participant"]
        p.setdefault("first_name", "")
        p.setdefault("last_name", "")
        p.setdefault("username", "")
        log("tgbot", "info", log_prefix + u"将 %s %s(@%s) 移除了该会话" % (p["first_name"], p["last_name"], p["username"]))
        return ""
    else:
        log("tgbot", "err", u"无法解析消息类型")
        raise Exception("Cannot parse msgType")

    log("tgbot", "err", u"未知的程序分支")
    raise Exception("Unknown situation")


def tgbot_processCmd(command, chat, user):
    c = command.split()
    if len(c) == 0:
        return "Please input command."

    if c[0] == "start":
        return "Hi, I'm Sakura.\nIf you call me from a group chat, I will ignore except you use \"@\" to notice me."

    if c[0] == "porn":
        return tgbot_aux_porn()

    if c[0] == "roll":
        name = "%s %s" % (user["first_name"], user["last_name"])
        if len(c) < 2:
            return tgbot_aux_roll(name, 6)

        if len(c[1]) > 10:
            return "Parameter <i>[max]</i> too long."
        else:
            return tgbot_aux_roll(name, c[1])

    if c[0] == "founder":
        return tgbot_aux_gettechidea()

    if c[0] == "nlp":
        if len(c) < 2:
            return "Need more parameter.\nUsage: /nlp <i>[Content]</i>"

        content = " ".join(c[1:])
        return tgbot_aux_nlp(content)

    if c[0] == "ip":
        if len(c) < 2:
            return "Need more parameter.\nUsage: /ip <i>[ip]</i>"

        return tgbot_aux_ip(c[1])

    if c[0] == "hitokoto":
        return tgbot_aux_hitokoto()

    if c[0] == "anime":
        return tgbot_aux_dmhy()

    if c[0] == "chatid":
        return str(chat["id"])

    if c[0] == "raisetest":
        raise Exception("This is a raise test")

    else:
        return "Command not found"


def tgbot_gen_responseText(chat, text, errormsg=False):
    if text == "":
        log("tgbot", "err", u"尝试发送空消息")
        raise Exception("Trying to send a empty msg")

    if errormsg:
        log("tgbot", "sys", u"检测到了一个错误并已告警")
        param = {"chat_id": tgbot_master_id, "text": text, "parse_mode": "HTML"}
        param["method"] = "sendMessage"
        return json.dumps(param)

    chatType = chat["type"]
    if chatType == "private":
        log_prefix = u"[私聊] %s=>%s %s(@%s): " % (tgbot_nickname, chat["first_name"], chat["last_name"], chat["username"])
    elif chatType == "group":
        log_prefix = u"[群消息] %s=>%s: " % (tgbot_nickname, chat["title"])
    elif chatType == "supergroup":
        log_prefix = u"[超级群] %s=>%s: " % (tgbot_nickname, chat["title"])
    elif chatType == "channel":
        log_prefix = u"[频道] %s=>%s (%s): " % (tgbot_nickname, chat["title"], chat["username"])
    else:
        log("tgbot", "err", u"回复时无法解析会话类型")
        raise Exception("Cannot parse chatType while response")

    log("tgbot", "msg", log_prefix + text)

    param = {"chat_id": chat["id"], "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    param["method"] = "sendMessage"
    return json.dumps(param)


def tgbot_api_sendMessage(chatID, text):
    param = {"chat_id": chatID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    postData = json.dumps(param)

    request = urllib2.Request("https://api.telegram.org/bot%s/sendMessage" % tgbot_token, postData)
    request.add_header("Host", "api.telegram.org")
    request.add_header('Content-Type', 'application/json')
    request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
    response = urllib2.urlopen(request)


def tgbot_aux_porn():
    try:
        requestBody = urllib2.Request("http://www.javlibrary.com/ja/vl_genre.php?g=ai&page=%s" % str(random.randint(1, 167)))
        requestBody.add_header("Cookie", "")
        requestBody.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
        requestBody.add_header("Referer", "http://www.javlibrary.com/")
        response = urllib2.urlopen(requestBody)

        m = re.findall('<div class="video".+?><a.+?title="(.+?)">', response.read(), re.DOTALL)
        if len(m) < 1:
            return "Porn recommendation service temporarily unavailable, please try again later.(Error 0)"
        return random.choice(m).decode("utf-8")
    except Exception, e:
        return "Porn recommendation service temporarily unavailable, please try again later.(Error 1)"


def tgbot_aux_roll(name, limit):
    try:
        maxset = int(limit)
        return u"%s rolls %s point(s)" % (name, str(random.randint(1, maxset)))
    except Exception:
        return "Parameter <i>[max]</i> needs a Integer to limit random range."


def tgbot_aux_gettechidea():
    leverage_list = [u"Bootstrap", u"大数据分析", u"云端技术", u"数据挖掘", u"机器学习", u"HTML5 标准", u"Web 2.0 标准", u"PaaS 框架", u"SaaS 框架", u"Facebook 图形 API", u"Node.js", u"Socket.io", u"Ruby on Rails", u"FireBase", u"Twitter API", u"DropBox API", u"Twilio API", u"Bilibili API", u"SendGrid API", u"RESTful API标准", u"MongoDB", u"Pebble watch", u"一个智能手表", u"一个四轴飞行器", u"图像处理", u"可调色阶的灯泡",
                     u"Leap Motion", u"Google Glass", u"Django", u"Flask", u"Objective-C", u"OCR技术", u"jQuery", u"AngularJS", u"D3.js", u"Xbox和Kinect", u"变异算法", u"遗传算法", u"Visual Basic", u"Backbone.js", u"触觉反馈技术", u"一个树莓派", u"Oculus Rift", u"虚拟现实技术", u"NoSQL", u"GPS定位技术", u"Unity", u"WebRTC", u"WebGL", u"计算机视觉技术", u"声音识别技术", u"太阳能技术", u"Scala", u"Bluetooth LE", u"手势识别技术", u"面部识别技术"]

    idea_prefix_list = [u"开源", u"实时", u"可动态调整", u"跨平台", u"创新", u"模块化", u"下一代", u"响应式", u"互动式", u"在线", u"环境友好型", u"新颖", u"综合", u"面向大学生的", u"基于地理位置的", u"移动端",
                        u"用户友好型", u"易于上手的", u"企业", u"改变行业现状的", u"直观的", u"前沿的", u"社交型", u"动态", u"协同", u"优化", u"分布式", u"协作式", u"可拓展的", u"可靠的", u"开源社区驱动的", u"并行处理", u"大规模并行"]

    idea_list = [u"虚拟现实", u"数据汇总", u"数据可视化", u"网页抓取", u"评测", u"分享", u"博客", u"医疗", u"卫生保健", u"人权保护", u"节能", u"医疗急救", u"灾难响应", u"捐助", u"慈善", u"音乐", u"绘画",
                 u"媒体", u"事件协调", u"教育", u"新闻", u"建站", u"电商", u"支付", u"贸易", u"旅行规划", u"内容管理", u"阅读", u"相片", u"互联网搜索", u"视频通话", u"短信息", u"通讯", u"导航", u"日程规划", u"健身", u"运动"]

    idea_type = [u"应用", u"web应用", u"游戏", u"平台", u"技术",
                 u"Chrome 插件", u"驱动引擎", u"解决方案", u"框架", u"系统", u"服务"]

    leverage_word_list = [u"借助", u"依赖", u"利用", u"通过", u"使用", u"整合", u"基于"]

    create_word_list = [u"做一个", u"开发", u"实现"]

    return u"%s%s%s%s%s%s" % (random.choice(leverage_word_list), random.choice(leverage_list), random.choice(create_word_list), random.choice(idea_prefix_list), random.choice(idea_list), random.choice(idea_type))


def tgbot_aux_nlp(text):
    try:
        postData = "url_path=http%3A%2F%2F10.209.0.215%3A55000%2Ftext%2Fclassify&body_data=%7B%22content%22%3A%22" + urllib.quote_plus(text.encode("utf-8")) + "%22%7D"
        requestBody = urllib2.Request("http://nlp.qq.com/public/wenzhi/api/common_api.php", postData)
        requestBody.add_header("Cookie", "")
        requestBody.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
        requestBody.add_header("Referer", "http://nlp.qq.com/semantic.cgi")
        requestBody.add_header("X-Requested-With", "XMLHttpRequest")
        requestBody.add_header("Origin", "http://nlp.qq.com")
        response = urllib2.urlopen(requestBody)
        html = response.read()
        d = json.loads(html)

        if d["ret_code"] != 0:
            return "NLP analysis service temporarily unavailable, please try again later. (Error 0)"

        rst = "NLP analyze result: "
        for cs in d["classes"]:
            rst = rst + cs["class"] + " "
        return rst

    except Exception:
        return "NLP analysis service temporarily unavailable, please try again later. (Error 1)"


def tgbot_aux_ip(ip):
    try:
        # location
        postData = "ip=" + urllib.quote_plus(ip.encode("utf-8"))
        requestBody = urllib2.Request("https://www.ipip.net/ip.html", postData)
        requestBody.add_header("Cookie", "")
        requestBody.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
        requestBody.add_header("Referer", "https://www.ipip.net/ip.html")
        requestBody.add_header("Origin", "https://www.ipip.net")
        response = urllib2.urlopen(requestBody)
        html = response.read()
        if u"请正确输入IP" in html.decode("utf-8"):
            return "Invalid IP."

        a = re.findall('<div>\s*<span id="myself">\s*([\W\w]*?)\s*</span>', html, re.DOTALL)
        l = re.findall('ip_data = {.+?"latitude":"(.+?)".+?":"(.+?)"', html, re.DOTALL)
        if len(a) < 1:
            return "IP info service temporarily unavailable, please try again later. (Error 0)"
        if len(l) == 2:
            return "IP info service temporarily unavailable, please try again later. (Error 1)"

        # human rate
        requestBodyb = urllib2.Request("https://ip.rtbasia.com/webservice/ipip?ipstr=" + ip)
        requestBodyb.add_header("Referer", "https://www.ipip.net/ip.html")
        responseb = urllib2.urlopen(requestBodyb)

        b = re.findall('<label.*?>(.*?)</label>', responseb.read(), re.DOTALL)

        if len(l) < 1:
            l = [(u"无数据", u"无数据")]
            ld = ""
        else:
            request = urllib2.Request("http://maps.google.com/maps/api/geocode/json?latlng=%s,%s&language=zh-CN&sensor=false" % (l[0][0], l[0][1]))
            request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
            response = urllib2.urlopen(request)
            j = json.loads(response.read())
            ld = j["results"][0]["formatted_address"]
        if len(b) < 1:
            b = [u"无数据"]

        # final
        return u"%s, %s, %s, %s" % (ip, a[0].decode("utf-8"), ld, b[0].decode("utf-8").replace("&nbsp;", ""))

    except Exception:
        return u"IP info service temporarily unavailable, please try again later. (Error 2)"


def tgbot_aux_hitokoto():
    try:
        request = urllib2.Request("http://api.hitokoto.us/rand")
        request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
        request.add_header("Referer", "http://webhook.iii.moe/telegram/bot")
        response = urllib2.urlopen(request)
        j = json.loads(response.read())

        if j["source"] == "":
            s = ""
        else:
            s = "(%s)" % j["source"]

        if j["author"] == "":
            a = u"无名"
        else:
            a = j["author"]

        return u"%s\n——%s %s" % (j["hitokoto"], a, s)

    except Exception:
        return "Hitokoto service temporarily unavailable, please try again later."


def tgbot_aux_dmhy():
    try:
        request = urllib2.Request("http://share.dmhy.org/")
        request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36")
        request.add_header("Cookie", "")
        request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        request.add_header("Accept-Language", "Accept-Language:zh-CN,zh;q=0.8")
        request.add_header("Cache-Control", "max-age=0")
        request.add_header("Host", "share.dmhy.org")
        request.add_header("If-Modified-Since", "Mon, 22 Feb 2016 11:18:37 GMT")
        response = urllib2.urlopen(request)

        a = re.findall('<td class="title">(?:<span.+?>.+?</span>)?.+?<a href="(.+?)".+?>(.+?)</a>', response.read(), re.DOTALL)

        rst = ""
        for b in a[0:7]:
            rst = rst + "<a href='http://share.dmhy.org%s'>%s</a>\n" % (b[0].replace("\n", "").replace("\t", ""), b[1].replace("\n", "").replace("\t", ""))
        return rst.decode("utf-8")

    except Exception:
        return "Latest anime service temporarily unavailable, please try again later."


def qqbot_main(jraw):
    j = json.loads(jraw)

    j.setdefault("group", "")

    msgSrcType = j["type"]
    msgSenderName = j["sender"]
    groupName = j["group"]
    text = j["content"]

    IS_PRIV = False
    IS_GROUP = False
    IS_SESS = False

    IS_SPECIAL = False

    tg_virtual_user = {"first_name": msgSenderName, "last_name": ""}
    tg_virtual_chat = {"id": ""}


    # Perpare log
    if msgSrcType == "message":
        log_prefix = u"[私聊] %s: " % msgSenderName
        IS_PRIV = True
        tg_virtual_chat["id"] = j["sender_id"]
    elif msgSrcType == "group_message":
        log_prefix = u"[群消息] %s|%s(%s): " % (msgSenderName, groupName, j["group_id"])
        IS_GROUP = True
        tg_virtual_chat["id"] = j["group_id"]
    else:
        log("qqbot", "err", u"无法解析会话类型")
        raise Exception("Cannot parse chatType")

    log("qqbot", "msg", log_prefix + j["content"])

    if ("@" + qqbot_nickname) in text:
        IS_SPECIAL = True

    text = text.replace("@" + qqbot_nickname, "")

    
    if (text[0] == "/" and IS_PRIV) or (text[0] == "/" and IS_SPECIAL): # 命令类，私聊和@bot的群聊，在这里转发到tgbot处理命令
            if IS_PRIV: qqbot_api_sendText(j["sender_id"], tgbot_processCmd(text[1:], tg_virtual_chat, tg_virtual_user))
            if IS_GROUP: qqbot_api_sendGroupText(j["group_id"], tgbot_processCmd(text[1:], tg_virtual_chat, tg_virtual_user))
            return ""
    elif IS_SPECIAL or IS_PRIV:
        return "" # @bot的群聊，或私聊时，在这里处理消息
    else: # 非@bot的群聊，在这里处理消息
        for qqgid, tggid in redirect_rules.iteritems():
            if qqgid == j["group_id"]:
                tgbot_api_sendMessage(tggid, u"QQ|%s: %s" % (msgSenderName, text))
                return ""
        return "" # 群不在转发列表中


def qqbot_api_sendText(qid, text):
    request = urllib2.Request("http://127.0.0.1:2333/openqq/send_message?id=%s&content=%s" % (qid, urllib.quote_plus(text.encode("utf-8"))))
    response = urllib2.urlopen(request)
    j = json.loads(response.read())

    log_prefix = u"[私聊] %s=>%s: " % (tgbot_nickname, qid)

    log("qqbot", "msg", log_prefix + text)
    if j["code"] != 0:
        raise Exception("qqbot API sendText Failed")


def qqbot_api_sendGroupText(gid, text):
    request = urllib2.Request("http://127.0.0.1:2333/openqq/send_group_message?gid=%s&content=%s" % (gid, urllib.quote_plus(text.encode("utf-8"))))
    response = urllib2.urlopen(request)
    j = json.loads(response.read())

    log_prefix = u"[群消息] %s=>%s : " % (tgbot_nickname, gid)

    log("qqbot", "msg", log_prefix + text)
    if j["code"] != 0:
        raise Exception("qqbot API sendGroupText Failed")


def log(hooktype, logtype, text):
    os.environ['TZ'] = 'Asia/Shanghai'
    time.tzset()  # Unix only
    print "[%s] [%s] [%s] %s" % (time.strftime("%Y/%m/%d %H:%M:%S"), hooktype, logtype, text.encode("utf-8"))


@app.route("/")
def index():
    return """<html><head><title>Hi</title><meta charset="UTF-8" /><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><meta http-equiv="X-UA-Compatible" content="IE=Edge,chrome=1" /><meta name="robots" content="noindex, nofollow" /><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1" /><style>body{font-family: "Microsoft YaHei","Helvetica Neue","STHeiti","STXihei";-webkit-font-smoothing: antialiased;margin: 0;padding: 0;color: #353535;}.preslot{float: left;height: 50%;margin-bottom: -200px;}.error{position: relative;clear: both;font-size: 200px;}.msg{font-size: 2.5em;margin-bottom: .5em;}.footer{clear: both;position: relative;color: #828282;}.des{color:#999999;font-size:1em;margin-bottom: 8em;}.link{color:#0084ff;text-decoration: none;transition: all 0.2s;}.link:hover{color:#ff8a00;transition: all 0.2s;}</style></head><body><center><div class="preslot"></div><div class="error">200</div><div class="msg">服务运行中</div><div class="des">Server Running</div><div class="footer">Powered by <a class="link" href="#">Stone</a></div></center></body></html>"""


@app.route(tgbot_url, methods=['POST'])
def tgbot():
    try:
        json_rst = tgbot_main(request.data)
        if json_rst == "":
            return ""
        else:
            return Response(json_rst, mimetype='application/json')
    except Exception:
        tb = traceback.format_exc()
        print tb
        return Response(tgbot_gen_responseText({}, u"<strong>故障告警:\nwebhook.iii.moe\ntgbot module</strong>\n========\n<i>Raw Json Recv:</i>\n<code>%s</code>\n\n<i>Traceback:</i>\n<code>%s</code>" % (request.data.decode("utf-8"), tb), True), mimetype='application/json')


@app.route(qqbot_url, methods=['POST'])
def qqbot():
    try:
        return qqbot_main(request.data)
    except Exception:
        tb = traceback.format_exc()
        print tb
        tgbot_api_sendMessage(tgbot_master_id, u"<strong>故障告警:\nwebhook.iii.moe\nqqbot module</strong>\n========\n<i>Raw Json Recv:</i>\n<code>%s</code>\n\n<i>Traceback:</i>\n<code>%s</code>" % (request.data.decode("utf-8"), tb))
        return ""


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8080)
    print "Deploying me with uwsgi"
