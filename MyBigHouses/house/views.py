from django.http import HttpResponse, JsonResponse
from .models import House, HistoryPrice
from django.views.generic import View
from django.db.models import Q
import pickle
from pymongo import MongoClient
from django_redis import get_redis_connection
import datetime
import json

# url: house/price/<city>/history?last_n_month=xx
class History(View):
    '''历史房价接口'''

    def __init__(self, **kwargs):
        with open("./house/city_mapping_e2c.pkl", "rb") as f:
            self.city_mapping = pickle.load(f)

    def get(self, request, city):
        # 检查是否有该城市
        location = self.city_mapping.get(city, None)
        if location is None:
            return JsonResponse({'code': 1, 'msg': "没有这个城市"})

        # 检查 '最近n月' 是否合法
        try:
            last_n_month = int(float(request.GET.get("last_n_month", 6)))

            if last_n_month <= 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'code': 2, 'msg': "不合法的年份信息"})

        # 查询数据库
        past_prices = HistoryPrice.objects.filter(location=location).order_by("-year", "-month")[:last_n_month]

        count = len(past_prices)  # 检索到的有效记录数
        prices = []
        for price in past_prices[::-1]:  # 数据汇总
            prices.append(['{}-{}'.format(price.year, price.month), str(price.average_price), str(price.tendency)])

        return JsonResponse({"code": 0, "count": count, "city": location, "data": prices})  # 返回 Json 响应

    def post(self):
        pass


# url:house/price/<city>/sub_location/
class CityInfoView(View):
    '''城市层级信息接口'''

    def __init__(self):
        with open("./house/city_mapping_e2c.pkl", "rb") as f:
            self.city_mapping = pickle.load(f)
            # 建立到 MongoDB 的连接
        client = MongoClient(host="42.159.122.43", port=27018)
        db = client.MBH
        self.city_relations = db.city_relations
        # 查询一次，存储在 cursor 中
        self.cursor = list(self.city_relations.find())[0]

    def get(self, request, location):
        # 英文转中文
        location_cn = self.city_mapping.get(location, None)
        if location_cn is None:
            return JsonResponse({"code": 1, "msg": "查询参数有误"})
        # 去数据库查询
        sub_location = self.cursor.get(location_cn, "None")
        # 返回数据
        if sub_location is None:
            return JsonResponse({"code": 2, "msg": "查无此城"})
        else:
            return JsonResponse({"code": 0, "data": sub_location}, safe=False)


# url:house/price/<city>/sub_location?last_n_month=n
# class SubLocationPriceView(View):
#     '''获取下级最新房价'''
#
#     def __init__(self):
#         with open("./house/city_mapping_e2c.pkl", "rb") as f:
#             self.city_mapping = pickle.load(f)
#             # 建立到 MongoDB 的连接
#         client = MongoClient(host="42.159.122.43", port=27018)
#         db = client.MBH
#         self.city_relations = db.city_relations
#         # 查询一次，存储在 cursor 中
#         self.cursor = list(self.city_relations.find())[0]
#
#     def get(self, request, city_name):
#         location_cn = self.city_mapping.get(city_name, None)
#         last_month = int(request.GET.get('last_n_month', 1))
#         if location_cn is None:
#             return JsonResponse({"code": 1, "msg": "没有这个城市"})
#
#         subs = self.cursor.get(location_cn, None)
#         if subs is None:
#             return JsonResponse({"code": 2, "msg": "已经到最后一级了"})
#         ret = [list() for i in range(last_month)]
#         date_time = list()
#         print(datetime.datetime.now())
#         for i, sub in enumerate(subs):
#             sub_info = HistoryPrice.objects.filter(location=sub).order_by("-year", "-month")[:last_month] # 只要最近 last_month 个月
#             if len(list(sub_info)) == 0:
#                 continue
#             else:
#                 for index in range(last_month):
#                     ret[index].append([sub_info[index].location, sub_info[index].average_price])
#                     if i == 0:
#                         date_time.append('{}-{}'.format(sub_info[index].year, sub_info[index].month))
#         print(datetime.datetime.now())
#         return JsonResponse({"code": 0, "data": ret, "location_cn": location_cn, "time": date_time})


# url:house/price/<city>/sub_location?year=xxxx&month=yy
class SubLocationPriceView(View):
    '''获取下级最新房价'''

    def __init__(self):
        with open("./house/city_mapping_e2c.pkl", "rb") as f:
            self.city_mapping = pickle.load(f)
            # 建立到 MongoDB 的连接
        client = MongoClient(host="42.159.122.43", port=27018)
        db = client.MBH
        self.city_relations = db.city_relations
        # 查询一次，存储在 cursor 中
        self.cursor = list(self.city_relations.find())[0]

    def get(self, request, city_name):
        location_cn = self.city_mapping.get(city_name, None)
        year = request.GET.get("year", None)
        month = request.GET.get("month", None)

        # 获取年份和月份信息
        if year is None:
            year = datetime.datetime.now().year

        if month is None:
            # 使用当前月
            cur_month = datetime.datetime.now().month
            # 格式化成数据库中存储的格式
            month = '0'+str(cur_month) if cur_month <= 9 else str(cur_month)
        else:
            if len(month) == 1:
                month = '0'+month

        if location_cn is None:
            return JsonResponse({"code": 1, "msg": "没有这个城市"})

        # 查询下属城镇信息
        subs = self.cursor.get(location_cn, None)
        if subs is None:
            return JsonResponse({"code": 2, "msg": "已经到最后一级了"})

        ret = [list()]
        date_time = list()

        for i, sub in enumerate(subs):
            sub_info = HistoryPrice.objects.filter(Q(location=sub) & Q(year=year) & Q(month=month))
            if len(list(sub_info)) == 0:
                continue
            else:
                ret[0].append([sub_info[0].location, sub_info[0].average_price])
                if i == 0:
                    date_time.append('{}-{}'.format(sub_info[0].year, sub_info[0].month))

        return JsonResponse({"code": 0, "data": ret, "location_cn": location_cn, "time": date_time})


# url:house/price/<city>/overview?number=x
class HouseOverView(View):
    def __init__(self):
        with open("./house/city_mapping_e2c.pkl", "rb") as f:
            self.city_mapping = pickle.load(f)
            # 建立到 MongoDB 的连接
        client = MongoClient(host="42.159.122.43", port=27018)
        db = client.MBH
        self.city_relations = db.city_relations
        # 查询一次，存储在 cursor 中
        self.cursor = list(self.city_relations.find())[0]

    def get(self, request, city_name):
        number = request.GET.get("number", None)
        location_cn = self.city_mapping.get(city_name, None)
        # 获取年份和月份信息
        if number is None:
            number = 4
        else:
            number = int(float(number))
        print(city_name)
        print(number)
        print(location_cn)
        overview_infos = list()
        infos = House.objects.filter(Q(city=location_cn) & ~Q(description='暂无描述') & ~Q(description='暂无该房源的描述'))[:number]
        for info in infos:
            print(info)
            overview_infos.append({'id': info.id, 'garden': info.garden, 'description': info.description,
                                   'area': info.area, 'total_price': info.total_price,
                                   'img_url': "require('@/assets/2.jpg')"})

        return JsonResponse({"code": 0, "data": overview_infos})


class HouseListFilterView(View):
    '''房子列表展示的地区筛选'''
    def __init__(self):
        with open("./house/city_mapping_e2c.pkl", "rb") as f:
            self.city_mapping = pickle.load(f)

    def get(self, request, city_name):
        location_cn = self.city_mapping.get(city_name, None)
        if location_cn is None:
            return JsonResponse({"code": 1, "msg": "查无此城市的次级信息"})

        records = House.objects.filter(city=location_cn)
        districts = records.values("district").distinct()
        districts = [district['district'] for district in districts]

        zones = dict()
        for district in districts:
            zone_queryset = records.filter(district=district).values("zone").distinct()
            zones[district] = [zone['zone'] for zone in zone_queryset]
        data = {'city': location_cn, 'districts': districts, 'zones': zones}
        return JsonResponse({"code": 0, 'data': data})


# url: house/detail/<house_id>
class HouseDetailView(View):
    '''房子详情信息接口'''

    def get(self, request, house_id):
        conn = get_redis_connection("User&House")
        try:
            session_user = json.loads(request.session['user'])
            user_id = session_user.get('id')
            user_key = "user_{}".format(user_id)

            # 检查是否已收藏
            star_list = conn.lrange(user_key, 0, -1)
            if str(house_id) in star_list:
                star_flag = True
            else:
                star_flag = False
        except KeyError:
            star_flag = False

        try:
            house = House.objects.get(id=house_id)
        except House.DoesNotExist:
            return JsonResponse({"code": 1, "msg": "<{}> 不存在".format(house_id)})

        # 增加浏览量计数
        house_key = "house_{}".format(house_id)
        conn.hincrby(house_key, "view_count", 1)
        view_count = int(conn.hget(house_key, "view_count").decode())
        # 获取该房子的收藏量
        star_count = conn.hget(house_key, "star_count")
        if star_count is None:
            star_count = 0
        else:
            star_count = star_count.decode()

        # 组装返回数据
        data = dict()
        data['description'] = house.description
        data['total_price'] = house.total_price
        data['price'] = house.price
        data['layout'] = house.layout
        data['orientation'] = house.orientation
        data['area'] = house.area
        data['layer'] = house.layer
        data['architecture'] = house.architecture
        data['built_year'] = house.built_year
        data['garden'] = house.garden
        data['location'] = "{} {}".format(house.district, house.zone)
        data['developer'] = house.developer
        data['property_company'] = house.property_company
        data['contact'] = '13800010001'

        return JsonResponse({"code": 0, "data": data, "view_count": view_count, "star_count": star_count, \
                             "star_flag": star_flag})