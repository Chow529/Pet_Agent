本项目为agent智能体,内嵌了rag,以及多智能体协同(未优化效率),tools
Open-Meteo(天气api)
serpApi(获取网页链接)----Jina Reader(获取网页内容)-->通过总结agent 获取 网页内容的文字描述总结
把web搜寻做成了tool
现在得流程用户->agent->调用summ->查询数据库->语义不匹配->调用网页搜索->返回结果给agent总结->返回给用户
搭建一个streamlit的前端界面,已有长期记忆,且进行了分id管理


其中网页搜索现在还不能搜索一直超时需要修改,