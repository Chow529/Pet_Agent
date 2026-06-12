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
from utils.logging_tool import logger
import re
import serpapi
import requests


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

@tool(description="从网上检索资料,入参是由逗号分割的关键词字符串")
def rag_webserch(querys:str) ->str:
    """
    根据关键词搜索网络资料
    
    Args:
        querys: 逗号分割的关键词字符串，例如 "狗狗呕吐,狗狗腹泻,宠物医疗"
    
    Returns:
        搜索结果字符串
    """
    keywords = [kw.strip() for kw in querys.split(',') if kw.strip()]
    
    if not keywords:
        return "未提供有效的搜索关键词"
    
    search_query = " ".join(keywords)
    
    # 你的 API Key
    api_key = "cdc835e69e3f05ca0bbc68e05cfa36573a919313570ed74190d78aabcbb8f4af"
    
    try:
        # 创建客户端
        client = serpapi.Client(api_key=api_key)
        
        # 执行搜索
        results = client.search({
            "engine": "google",
            "q": search_query,
            "hl": "zh-cn",      # 中文
            "gl": "cn",         # 中国地区
            "num": 5            # 返回5条结果
        })
        
        # 提取有机搜索结果
        organic_results = results.get("organic_results", [])
        
        if not organic_results:
            return f"未找到关于「{search_query}」的相关信息"
        
        # 格式化结果
        formatted = f"关于「{search_query}」的搜索结果：\n\n"
        for i, item in enumerate(organic_results[:2], 1):
            
            link = item.get("link", "")
            print("*"*20,f"link:  {link}","*"*20)
            if link:
                formatted += f"{i}. {fetch_with_jina(link)}\n"
            formatted += "\n"
        
        return formatted
        
    except Exception as e:
        return f"搜索失败：{str(e)}"
    
def fetch_with_jina(url: str, max_chars: int = 2000) -> str:
    """使用 Jina Reader 获取网页内容（带完整错误处理）"""
    
    # 验证 URL
    if not url or not url.startswith(('http://', 'https://')):
        url = 'https://' + url if url else ''
        if not url:
            return ""
    
    # 获取 API 密钥
    jina_api_key = "jina_67de777337ed4867bc5a0dd2af4b59936uRJ_KsY0nPpTx-gIpwNBlahLfFA"
    
    if not jina_api_key:
        error_msg = (
            "未配置 Jina API 密钥。\n"
            "请按以下步骤配置：\n"
            "1. 访问 https://jina.ai/ 注册账号\n"
            "2. 在 Dashboard 创建 API Key\n"
            "3. 在项目根目录创建 .env 文件\n"
            "4. 添加 JINA_API_KEY=your_key_here"
        )
        logger.error(error_msg)
        return ""
    
    try:
        reader_url = f"https://r.jina.ai/{url}"
        
        headers = {
            "Authorization": f"Bearer {jina_api_key}",
            "Accept": "text/plain",
            "X-Timeout": "30"  # 设置 Jina 服务端超时
        }
        
        response = requests.get(reader_url, headers=headers, timeout=15)
        
        # 处理各种状态码
        if response.status_code == 200:
            content = response.text
            
        elif response.status_code == 401:
            logger.error("Jina API 密钥无效，请检查环境变量 JINA_API_KEY")
            return ""
            
        elif response.status_code == 402:
            logger.error("Jina API 配额已用完")
            return ""
            
        elif response.status_code == 429:
            logger.error("请求过于频繁，请稍后再试")
            return ""
            
        else:
            logger.error(f"Jina Reader 返回错误: {response.status_code}")
            return ""
        
        # 清理内容
        clean_text = clean_jina_content(content)
        
        # 限制长度
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "..."
        
        print("|"*20,clean_text,"|"*20)
        return clean_text.strip()
        
    except requests.Timeout:
        logger.error("Jina Reader 请求超时")
        return ""
    except Exception as e:
        logger.error(f"Jina Reader 获取失败: {e}")
        return ""

def clean_jina_content(content: str) -> str:
    """清理 Jina Reader 返回的内容"""
    # 跳过 YAML 头
    if '---\n' in content:
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            content = parts[2]
    
    # 清理链接 [text](url) -> text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # 移除标题标记
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
    
    # 移除列表标记
    content = re.sub(r'^[\s]*[•\-*]\s+', '', content, flags=re.MULTILINE)
    
    # 移除多余空行
    content = re.sub(r'\n\s*\n', '\n\n', content)
    print("-"*20,content,"-"*20)
    return content.strip() 


# if __name__ == "__main__" :
#     print(rag_webserch("宠物,医疗,呕吐"))