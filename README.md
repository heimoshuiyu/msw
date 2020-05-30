# MSW
简单网络框架  
README暂时写中文，英文水平差容易产生歧义orz...  

# 介绍
- 程序会自动载入`plugins`文件夹内所有python脚本，换言之，所有自定义插件都可以放到plugins目录中
- 程序会为每一个plugin提供一个独立的接收队列`recive_queue`，插件可以通过调用`recive_queue.get()`获取数据
- 程序为所有plugin提供一个共用的发送队列`send_queue`，插件可以通过调用`send_queue.put()`来使用框架发送数据
- “数据”，是指`mswp.py`中定义的`Datapack`类型，这种结构储存了数据包发送目的地、来源、参数等信息
- `forwarder.py`会读取`send_queue`，判断“数据”中的`app`这一项属性，将其放到对应plugin的接收队列中，起到路由的作用  
总的来说  
plugin完成某项任务后，创建`Datapack`对象并设置好该数据包的发送目的地等参数，将其放入到`send_queue`中，对应plugin就可以收到该数据包  

# 部署
部署很简单，把文件下载下来，写好配置直接运行
## 安装
运行命令克隆仓库  
> `git clone https://github.com/heimoshuiyu/msw`

## 配置config.json
配置`config.json`中的`id`，监听地址、端口等信息  
单台机器可以运行多个msw，只要配置不同的id和监听端口接口
## 配置地址列表
编辑创建`address.txt`，格式请参考`address_example.txt`
## 运行
> `python main.py`

或者
> `python3 main.py`

注意：msw仅支持python3

# 数据包Datapack
msw中队列传递的都是一种叫Datapack的结构，其结构类似http的请求包（由`mswp.py`定义）  
示例  

````
post shell msw/0.1
from: test
id: hmsy
to: miku
flag: 1a2b3c4d

shutdown now
````

- 解释：向名为`miku`的主机的`shell`插件发送`shutdown now`的命令，执行结果返回到`hmsy`主机的`test`插件
- `Datapack.method`有三种可能的值：`post`、`reply`、`file`
    - `post`是最普通的，一般数据包都使用该标识
    - `reply`标记该数据包是一个回复
    - `file`标记该数据包是一个文件，文件由`filename`参数指定，数据包中不会包含文件的内容
- `Datapack.app`表示数据包发送目的地的plugin名字，如`shell`，即`plugins/shell.py`该程序会收到此数据包
    - 若是找不到对应app，则产生一个警告
- `Datapack.version`表示当前程序版本，暂时还没什么用
- `Datapack.head`一个字典，储存参数
    - `to`若存在，参数表示这是一个需要网络发送的数据包，数据包会被发送到`to`指定的主机
    - `id`表示发送人的id，由程序自动配置
    - `from`表示发送的插件名，`reply`方法会用到这个参数，建议设置为`__name__`
    - `flag`数据包识别码，由程序随机自动生成，调试用，暂无特殊用途
    - `filename`，仅在`Datapack.method`为`file`时生效，
- `Datapack.body`数据包主内容

# 已实现功能
- `main.py`
    - 这是一个守护程序，会调用`os.system()`来运行`msw.py`主程序，主程序若正常退出（返回值0）则重启主程序
- `forwarder.py`
    - 在`send_queue`和`recive_queues`中实现转发功能
    - 根据`Datapack.app`选择队列进行转发
    - 如果参数中包含`to`这一项，将转发给`plugins/net.py`，由net插件进行网络转发
- `plugins/update.py`
    - 依赖`plugins/net.py`，可以快读更新其他主机的代码
    - 该插件可以将程序目录下的文件过滤并打包，然后发送给其他主机
    - 其他主机收到文件，会解压并替换程序原有文件，然后向msw发送0值尝试重启
- `plugins/input.py`
    - 循环调用`input()`，允许用户输入命令
    - 命令格式`插件名:数据包内容;键:值,键2:值2`
    - 例如`update:compress;update_to:*`表示向`plugins/update`发送内容为`compress`，参数`update_to=*`的数据包。`compress`和`update_to`字段都是plugins/update.py中定义的，`compress`表示压缩,update表示解压缩，`update_to`表示将升级包发送到这个目录，设置为*表示所有主机，*的功能是在`plugins/net.py`中定义的
- `plugins/net.py`
    - 网络插件，读取`address.txt`中的地址并连接，和其他主机交换地址列表，建立类似dht的网络
    - 如果`Datapack`中含有参数`to`，`forward.py`会无条件将数据包转发到此插件进行网络发送，发送完成后会去掉`to`参数
    - 插件收到其他主机发来的数据包，解码后会放进`send_queue`队列中，如果此时还存在`to`参数，会进行多次转发，实现代理功能
    - 反向代理：插件根据`to`参数确定主机地址，`to`参数内容为主机id，若在连接池中有该id的连接则直接发送，否则参考proxy字典决定是否发送给代理，否则放入发送失败队列等待重发
    - 发送文件：`Datapack.method`为`file`时启动，根据`filename`参数中制定的文件进行发送
    - 接受文件：文件下载完成后才会将数据包放入`send_queue`队列中
    - 心跳&mht：定时交换自身拥有的地址列表、代理列表
    - 重试失败次数超过39次，数据包将被丢弃
- `plugins/ffmpeg.py`
    - 分布式转码
    - 调用系统ffmpeg，对视频进行切片，分发，转码，收集合并
    - 对分发主机启动server模式并指定文件名，对转码主机启动worker模式并指定分发主机的id，即可开始转码
- `plugins/logger.py`
    - 日志记录，会将接收到的数据包写入`log.txt`

# 编写第一个插件
建议参考`plugins/logger.py`，这个简单的日志记录器实现了数据包的接受和发送
## 示例代码
````python
import threading
from forwarder import recive_queues, send_queue
from mswp import Datapack
# 获取自身对应的接受队列
recive_queue = recive_queues[__name__]

def main():
    while True:
        dp = recive_queue.get() # 阻塞获取数据包
        if dp.method = 'post': # 打印出数据包的head和body
            print('You recive head is', str(dp.head))
            print('You recive body is', dp.body.decode())
        if dp.method = 'post': # 回复数据包示例
            ndp = dp.reply()
            ndp.body = 'recived'.encode()
            send_queue.put(ndp) # 发送数据包
        else: # 新建数据包示例
            dp = Datapack(head={'from'=__name__})
            dp.head['to'] = 'hmsy' # 设置目标主机名
            send_queue.put(dp)
            # 发送文件示例
            dp = Datapack(head={'from'=__name__})
            dp.method = 'file' # 标记该数据包为文件类型
            dp.head['to'] = 'hsmy'
            dp.head['filename'] = 'res/file.txt'  # 设置数据包携带的文件
            send_queue.put(dp)
            

# 必须以多线程方式启动主函数，必须设置daemon让主线程退出后，子线程也能退出
thread = threading.Thread(target=main, args=(), daemon=True)
thread.start()
````
原则上不建议直接import其他plugin，建议通过发送Datapack来与其他插件交互
