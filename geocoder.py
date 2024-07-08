# -*- coding:utf-8 -*-
# @Author: H
# @Date: 2024-07-08 10:56:04
# @Version: 1.0
# @License: H
# @Desc: 
import os
import geopandas as gpd
from shapely.geometry import Point

class GeoCoder:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GeoCoder, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self, cache=True):
        # 是否使用缓存，是：geo数据会加载到内存，但查询速度快；否：每次查询都会重新加载geo数据，占用内存较少，但查询速度较慢
        self.cache = cache
        self.geo_gdf = {}

        # 加载 GeoJSON 数据文件
        self.DIR_BASE = os.path.dirname(os.path.abspath(__file__))
        self.base_gdf = gpd.read_file(os.path.join(self.DIR_BASE, 'geodata','china.json'))

    def get_point_df(self, gdf, point):
        if gdf is None:
            return None
        for idx, row in gdf.iterrows():
            if row['geometry'].buffer(0).contains(point):
                return row
        return None

    def get_gdf(self, type, code):
        path = os.path.join(self.DIR_BASE,'geodata',type, f'{code}.json')
        if not os.path.exists(path):
            return None
        if self.cache:
            if code in self.geo_gdf:
                return self.geo_gdf[code]
            else:
                gdf = gpd.read_file(path)
                self.geo_gdf[code] = gdf
                return gdf
        else:
            gdf = gpd.read_file(path)
        return gdf


    def point_to_location(self, longitude, latitude):
        # 根据经纬度获取 省份、城市、区县

        # 空间查询找出包含该点的区域
        prov_name, prov_code, city_name, city_code, district_name, district_code = '', '', '', '', '', ''
        try:
            longitude, latitude = float(longitude), float(latitude)
        except Exception as e:
            assert  False, f'经纬度格式错误: {longitude}, {latitude}'
        
        point = Point(longitude, latitude)
        prov_df = self.get_point_df (self.base_gdf, point)
        if prov_df is not None:
            prov_code = str(prov_df['adcode'])
            prov_name = prov_df['name']

            city_gdf = self.get_gdf('province', prov_code)
            city_df = self.get_point_df(city_gdf, point)
            if city_df is not None:
                city_code = str(city_df['adcode'])
                city_name = city_df['name']
                
                # 直辖市处理
                if prov_name in {'北京市', '上海市', '天津市', '重庆市'}:
                    district_name = city_name
                    district_code = city_code
                    city_name = prov_name
                    city_code = prov_code
                else:
                    district_gdf = self.get_gdf('citys', city_code)
                    district_df = self.get_point_df(district_gdf, point)
                    district_name = district_df['name'] if district_df is not None else ''
                    district_code = district_df['adcode'] if district_df is not None else ''

        return {'prov_name': prov_name, 
                'prov_code': prov_code,
                'city_name': city_name,
                'city_code': city_code,
                'district_name': district_name,
                'district_code': district_code
                }
    
if __name__ == '__main__':
    g = GeoCoder()
    print(g.point_to_location(104.066541, 30.572269))
