# RASA法律助手项目:CaseAssitant
利用天气查询的

# 1. 环境配置
&emsp;最好创建一个虚拟环境，之后再虚拟环境中运行命令：pip install -r requirements.txt。

- python 3.6 +
- rasa 1.9.5
- mitie
- jieba
- neo4j(optional)

# 2. 训练模型  

&emsp;打开命令终端执行下面的命令，该命令会同时训练NLU和Core模型。

- 使用MITIE

```shell
python -m rasa train --config configs/config.yml --domain configs/domain.yml --data data/
```

- 使用supervised embedding

```bash
python -m rasa train --config configs/zh_jieba_supervised_embeddings_config.yml --domain configs/domain.yml --data data/
```

- 使用MITIE supervised embedding

```bash
python -m rasa train --config configs/zh_jieba_mitie_embeddings_config.yml --domain configs/domain.yml --data data/
```

# 3. 运行服务  

**（1）启动Rasa服务**

&emsp;在命令终端，输入下面命令：

```shell
# 启动rasa服务
# 该服务实现自然语言理解(NLU)功能
# 注：该服务的--port默认为5005，如果使用默认则可以省略
python -m rasa run --port 5005 -m models/20210525-135302.tar.gz --endpoints configs/endpoints.yml --credentials configs/credentials.yml --debug
```

**（2）启动Action服务**

在命令终端，输入下面命令：

```shell
# 启动action服务对话管理(Core)功能
# 注：该服务的--port默认为5055，如果使用默认则可以省略
python -m rasa run actions --port 5055 --actions actions --debug
```

**（3）启动server.py服务**

```shell
python server.py
```

当**Rasa Server**、**Action Server**和**Server.py**运行后，在浏览器输入测试：

` http://127.0.0.1:8088/ai?content=查询广州明天的天气`


# 4. 更新日志

**（1）V1.0.2021.05.15**

- 创建项目，模型训练成功；
- 前端访问Rasa服务器正常响应；
- 对接图灵闲聊机器人、心知天气API，便于测试；

**（2）V1.1.2021.05.22**

- 加入案例相关数据；


