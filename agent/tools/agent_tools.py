import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime
from langchain_core.tools import tool

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent


sys.path.insert(0, str(project_root))

from rag.RagService import rag
from utils.file_tool import rag_webserch


@tool(description="从向量库里面检索参考资料")
def rag_summarize(query:str) ->str:
    return rag.rag_summarize(query)


# 配置缓存和重试机制
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session   = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session = retry_session) # type: ignore

@tool(description="获取某地某一时刻的天气情况")
def get_weather(location:str,date :str) ->str:
    """
    根据城市名称和日期获取天气（支持过去、现在和未来）
    
    Args:
        location: 城市名称，如"北京"、"上海"、"London"
        date: 日期，格式为 YYYY-MM-DD（支持 1940 年至今的历史数据，以及未来 16 天预报）
    
    Returns:
        格式化的天气信息字符串
    """
    # 步骤1：通过 Geocoding API 获取城市坐标
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    geocode_params = {
        "name": location,
        "count": 1,
        "language": "zh",
        "format": "json"
    }
    
    try:
        import requests
        geo_response = requests.get(geocode_url, params=geocode_params, timeout=10)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
    except Exception as e:
        return f"查询城市坐标时发生错误：{e}"
    
    if not geo_data.get("results"):
        return f"未找到城市“{location}”，请检查城市名称是否正确。"
    
    city_info = geo_data["results"][0]
    city_name = city_info.get("name", location)
    country = city_info.get("country", "")
    lat = city_info["latitude"]
    lon = city_info["longitude"]
    
    # 步骤2：解析日期
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        return f"日期格式错误，请使用 YYYY-MM-DD 格式"
    
    # 步骤3：根据日期类型调用不同的 API
    if query_date > today:
        # 未来日期：使用 forecast API
        days_ahead = (query_date - today).days
        if days_ahead > 16:
            return f"抱歉，最多只能查询未来16天的天气。您查询的是 {days_ahead} 天后的天气。"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
            "forecast_days": days_ahead + 1,
            "timezone": "auto"
        }
        responses = openmeteo.weather_api("https://api.open-meteo.com/v1/forecast", params=params)
        date_type = "天气预报"
        
    else:
        # 过去或今天：使用 history API
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
            "start_date": query_date.strftime("%Y-%m-%d"),
            "end_date": query_date.strftime("%Y-%m-%d"),
            "timezone": "auto"
        }
        responses = openmeteo.weather_api("https://archive-api.open-meteo.com/v1/archive", params=params)
        
        if query_date < today:
            date_type = "历史天气"
        else:
            date_type = "今日天气"
    
    # 处理响应
    response = responses[0]
    
    # 获取 daily 数据
    daily = response.Daily()
    daily_temperature_max = daily.Variables(0).ValuesAsNumpy() # type: ignore
    daily_temperature_min = daily.Variables(1).ValuesAsNumpy() # type: ignore
    daily_weather_code = daily.Variables(2).ValuesAsNumpy() # type: ignore
    
    # 获取对应日期的数据（索引0）
    temp_max = daily_temperature_max[0]
    temp_min = daily_temperature_min[0]
    weather_code = int(daily_weather_code[0])
    
    # # 天气代码映射表 (WMO code)
    # weather_desc = {
    #     0: "晴天 ☀️", 1: "基本晴天 🌤️", 2: "局部多云 ⛅", 3: "阴天 ☁️",
    #     45: "雾天 🌫️", 48: "雾凇雾天 🌫️",
    #     51: "小雨 🌧️", 53: "中雨 🌧️", 55: "大雨 🌧️",
    #     56: "冻小雨 🌧️❄️", 57: "冻大雨 🌧️❄️",
    #     61: "小雨 🌧️", 63: "中雨 🌧️", 65: "大雨 🌧️",
    #     66: "冻小雨 🌧️❄️", 67: "冻大雨 🌧️❄️",
    #     71: "小雪 ❄️", 73: "中雪 ❄️", 75: "大雪 ❄️",
    #     77: "雪粒 ❄️",
    #     80: "小阵雨 🌦️", 81: "中阵雨 🌦️", 82: "大阵雨 🌧️",
    #     85: "小阵雪 ❄️", 86: "大阵雪 ❄️",
    #     95: "雷暴 ⛈️", 96: "雷暴伴小雹 ⛈️", 99: "雷暴伴大雹 ⛈️"
    # }.get(weather_code, "未知天气")
    
    return f"{city_name}({country}){date_type}({date}):{weather_code}，温度:{temp_min:.1f}°C ~ {temp_max:.1f}°C"
    

if __name__ == "__main__" :
    print(rag_webserch("宠物,医疗,呕吐"))