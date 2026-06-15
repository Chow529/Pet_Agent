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
import os
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

    # 从环境变量读取 SerpAPI Key
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "未配置 SERPAPI_API_KEY 环境变量，请在 .env 文件中设置"
    
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
        for i, item in enumerate(organic_results, 1):
            
            link = item.get("link", "")
            print("*"*20,f"link:  {link}","*"*20)
            if link:
                formatted += f"{i}. {fetch_with_jina(link)}\n"
            formatted += "\n"
        
        return formatted
        
    except Exception as e:
        return f"搜索失败：{str(e)}"
    
def fetch_with_jina(url: str, max_chars: int = 2000) -> str:
    """增强版网页抓取，模拟真实浏览器"""
    
    if not url or not url.startswith(('http://', 'https://')):
        url = 'https://' + url if url else ''
        if not url:
            return ""
    
    try:
        # 更完整的浏览器请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Connection": "keep-alive",
        }
        
        # 使用会话保持连接
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(url, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # 处理压缩内容
        if response.encoding is None:
            response.encoding = response.apparent_encoding
        
        # 使用 lxml 解析 HTML
        from lxml import html
        doc = html.fromstring(response.content)
        
        # 移除无用元素
        for tag in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']:
            for element in doc.xpath(f'//{tag}'):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
        
        # 优先提取 article / main 区域的内容
        body = doc.xpath('//article | //main | //div[@class="content"] | //div[@class="post-content"] | //body')
        if body:
            text = body[0].text_content()
        else:
            text = doc.text_content()
        
        # 清理文本
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 1 and not line.startswith(('{', '}', '【', '】')):
                # 过滤掉明显的JSON或模板代码
                lines.append(line)
        
        clean_text = '\n'.join(lines)
        
        # 去除过长的空白行
        import re
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        
        # 限制长度
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "..."
        
        return clean_text.strip()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(f"网站拒绝访问 [{url}]: 可能需要添加Cookie")
            return f"[该网站需要验证，无法获取内容: {url}]"
        elif e.response.status_code == 429:
            logger.warning(f"请求频率过高 [{url}]")
            return f"[请求过于频繁，请稍后再试: {url}]"
        else:
            logger.error(f"HTTP错误 [{url}]: {e}")
            return ""
    except Exception as e:
        logger.error(f"网页获取失败 [{url}]: {e}")
        return ""

def clean_jina_content(content: str) -> str:
    """清理网页原始内容（兼容旧调用，目前直接返回原始内容）"""
    return content.strip()



if __name__ == "__main__" :
    print(rag_webserch("宠物,医疗,呕吐"))