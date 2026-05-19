# 串口透明转发项目（Python + Socket.IO + Vue2）

## 功能
- 后端接收串口数据并实时推送到前端。
- 后端接收前端指令并写入串口，再将串口返回数据推送前端。
- 透明转发：不解析业务协议。
- 串口粘包处理：基于分隔符（默认 `\n`）进行拆包。
- Socket增强：心跳检测、自动重连（客户端）、ACK 消息确认机制。

## 后端
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

环境变量：
- `SERIAL_PORT` 默认 `COM1`
- `SERIAL_BAUDRATE` 默认 `115200`
- `SERIAL_TIMEOUT` 默认 `0.1`
- `SOCKETIO_PING_INTERVAL` 默认 `25`
- `SOCKETIO_PING_TIMEOUT` 默认 `60`

## 前端
```bash
cd frontend
npm install
npm run serve
```

默认连接 `http://localhost:8000`。
