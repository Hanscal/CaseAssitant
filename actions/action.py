from typing import Dict, Text, Any, List, Union
from requests import (ConnectionError, HTTPError, TooManyRedirects, Timeout)
from py2neo import Graph, NodeMatcher

from rasa_sdk import Tracker, Action
from rasa_sdk.events import UserUtteranceReverted, Restarted, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction

# 闲聊模块以及天气查询模块
from actions import ChatApis
from actions.WeatherApis import get_weather_by_day

graph = Graph(host="127.0.0.1", http_port=7474, user="neo4j", password="CHneo4j")
selector = NodeMatcher(graph)

class NumberForm(FormAction):
    """Example of a custom form action"""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "number_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["type", "number", "business"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "type": self.from_entity(entity="type", not_intent="chitchat"),
            "number": self.from_entity(entity="number", not_intent="chitchat"),
            "business": [
                self.from_entity(
                    entity="business", intent=["inform", "request_number"]
                ),
                self.from_entity(entity="business"),
            ],
        }

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        number_type = tracker.get_slot('type')
        number = tracker.get_slot('number')
        business = tracker.get_slot('business')
        if not business:
            dispatcher.utter_message(text="您要查询的{}{}所属人为张三，湖南长沙人，现在就职于地球村物业管理有限公司。".format(number_type, number))
            return []

        dispatcher.utter_message(text="你要查询{}为{}的{}为：balabalabalabalabala。".format(number_type, number, business))
        return [SlotSet("business", None)]


class WeatherForm(FormAction):

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "weather_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["date_time", "address"]

    def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        address = tracker.get_slot('address')
        date_time = tracker.get_slot('date_time')

        date_time_number = text_date_to_number_date(date_time)

        if isinstance(date_time_number, str):  # parse date_time failed
            dispatcher.utter_message("暂不支持查询 {} 的天气".format([address, date_time_number]))
        else:
            weather_data = get_text_weather_date(address, date_time, date_time_number)
            dispatcher.utter_message(weather_data)
        return []


def get_text_weather_date(address, date_time, date_time_number):
    try:
        result = get_weather_by_day(address, date_time_number)
    except (ConnectionError, HTTPError, TooManyRedirects, Timeout) as e:
        text_message = "{}".format(e)
    else:
        text_message_tpl = """
            {} {} ({}) 的天气情况为：白天：{}；夜晚：{}；气温：{}-{} °C
        """
        text_message = text_message_tpl.format(
            result['location']['name'],
            date_time,
            result['result']['date'],
            result['result']['text_day'],
            result['result']['text_night'],
            result['result']["high"],
            result['result']["low"],
        )

    return text_message


def text_date_to_number_date(text_date):
    if text_date == "今天":
        return 0
    if text_date == "明天":
        return 1
    if text_date == "后天":
        return 2

    # Not supported by weather API provider freely
    if text_date == "大后天":
        # return 3
        return text_date

    if text_date.startswith("星期"):
        # TODO: using calender to compute relative date
        return text_date

    if text_date.startswith("下星期"):
        # TODO: using calender to compute relative date
        return text_date

    # follow APIs are not supported by weather API provider freely
    if text_date == "昨天":
        return text_date
    if text_date == "前天":
        return text_date
    if text_date == "大前天":
        return text_date


class ActionDefaultFallback(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self):
        return 'action_default_fallback'

    def run(self, dispatcher, tracker, domain):

        # 访问图灵机器人API(闲聊)
        text = tracker.latest_message.get('text')
        message = ChatApis.get_response(text)
        if message is not None:
            dispatcher.utter_message(message)
        else:
            dispatcher.utter_template('utter_default', tracker, silent_fail=True)
        return [UserUtteranceReverted()]




def retrieveDataFromNeo4j(cyber):
    data = graph.run(cyber)
    return data

# 查看案例被告
class ViewCaseDefendants(Action):
    def name(self):
        return 'action_view_case_defendants'

    def run(self, dispatcher, tracker, domain):
        case = tracker.get_slot('case')
        if (case == None):
            dispatcher.utter_message("服务器开小差了")
            return []
        all_defendants = ""
        a = list(selector.match("被告人", 案件号__contains=case))
        for _ in a:
            if (a[a.__len__() - 1] == _):
                all_defendants = all_defendants + _['name'] + "."
            else:
                all_defendants = all_defendants + _['name'] + ','
        response = "{}案件, 有涉案人员:{}".format(case, all_defendants)
        dispatcher.utter_message(response)
        return [SlotSet('case', case)]


# 查看涉案人员
class ViewCaseDefendantsNum(Action):
    def name(self):
        return 'action_view_case_defendants_num'

    def run(self, dispatcher, tracker, domain):
        case = tracker.get_slot('case')
        if (case == None):
            dispatcher.utter_message("服务器开小差了")
            return []
        # n = list(selector.match("被告人", 案件号__contains=case)).__len__()
        cyber = """MATCH (n) WHERE n.`案件号` CONTAINS "{}" return n""".format(case) # STARTS WITH, ENDS WITH, CONTAINS
        n = list(graph.run(cyber))
        if (n.__len__() == 0):
            response = "没有这个案件, 查证后再说吧~"
        else:
            # 需要对案件人员进行去重
            defendants = set([i['n']['name'] for i in n])
            response = "{}案件共有{}个涉案人员:{}".format(case, len(defendants),','.join(defendants))
        # graph_data = retrieveDataFromNeo4j("MATCH path = (n)-[r]->(m) where n.案件号 =~ '.*{}.*' RETURN path".format(case))
        dispatcher.utter_message(response)
        return [SlotSet('case', case)]


# 查看被告信息
class ViewDefendantData(Action):
    def name(self):
        return 'action_view_defendant_data'

    def run(self, dispatcher, tracker, domain):
        defendant = tracker.get_slot('defendant')
        item = tracker.get_slot('item')
        # person = graph.nodes.match("被告人", name=defendant).first()
        cyber = """MATCH (n:`被告人`) WHERE n.name="{}" return n""".format(defendant)
        person = list(graph.run(cyber))
        response = "这个系统还够完善, 没有找到{}关于'{}'的信息, 抱歉哦..".format(defendant, item)
        if (item == None or defendant == None):
            dispatcher.utter_message("服务器开小差了")
            return []

        # < id >: 0
        # name: 张青红出生地: 浙江省云和县出生日期: 1979
        # 年8月14日性别: 女户籍所在地: 云和县凤凰山街道上前溪100号文化程度: 初中文化案件号: （2017）浙1125刑初148号毒品数量: 31.3
        # 克民族: 汉族现住址: 丽水市莲都区水阁工业区齐垵村20号2楼职业: 务工
        if person:
            person = person[0]['n']
            if item.find("个人资料") != -1:
                response = "{},{},{}生,户籍所在:{}, {}程度, 现住{}, 贩毒{}".format(defendant, person['性别'], person['出生日期'],
                                                                        person['户籍所在地'], person['文化程度'], person['现住址'],
                                                                        person['毒品数量'])
            elif item.find("出生地") != -1:
                response = "{}的出生地是:{}".format(defendant, person['出生地'])
            elif item.find("生日") != -1:
                response = "{}的生日是:{}".format(defendant, person['出生日期'])
            elif item.find("性别") != -1:
                response = "{}的性别是:{}".format(defendant, person['性别'])
            elif item.find("户籍所在地") != -1:
                response = "{}的户籍所在地是:{}".format(defendant, person['户籍所在地'])
            elif item.find("文化程度") != -1:
                response = "{}的文化程度是:{}".format(defendant, person['文化程度'])
            elif item.find("贩毒量") != -1:
                response = "{}的贩毒量是:{}".format(defendant, person['毒品数量'])
            elif item.find("民族") != -1:
                response = "{}的民族是:{}".format(defendant, person['民族'])
            elif item.find("现住址") != -1:
                response = "{}的现住址是:{}".format(defendant, person['现住址'])
            elif item.find("职业") != -1:
                response = "{}的职业是:{}".format(defendant, person['职业'])

        # graph_data = retrieveDataFromNeo4j("MATCH path = (n)-[r]->(m) where n.name =~ '.*{}.*' RETURN path".format(defendant))
        dispatcher.utter_message(response)
        return [SlotSet('defendant', defendant)]


# 查看案件详情
class ViewCaseDetail(Action):  # TODO
    def name(self):
        return 'action_view_case_detail'

    def run(self, dispatcher, tracker, domain):
        case = tracker.get_slot('case')
        if (case == None):
            dispatcher.utter_message("服务器开小差了")
            return []
        found = graph.nodes.match("被告人", 案件号__contains=case)
        n = list(found).__len__()
        if (n == 0):
            response = "没有找到这个案件, 是不是案件号错了"
        else:
            response = '没有找到'
            # graph_data = retrieveDataFromNeo4j("MATCH path = (n)-[r]->(m) where n.案件号 =~ '.*{}.*' RETURN path".format(case))
        dispatcher.utter_message(response)
        return [SlotSet('case', case)]