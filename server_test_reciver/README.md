# Setup Nginx cho staging.vandat.io.vn

**Ngày thực hiện**: 27/11/2025 08:56 - 09:00 (+07:00)

## ✅ Tóm Tắt

Đã hoàn thành setup nginx cơ bản cho domain `staging.vandat.io.vn`. Nginx đã được cài đặt và cấu hình thành công, sẵn sàng phục vụ frontend, WebSocket, HTTP API và gRPC.

## 📋 Chi Tiết Các Bước Đã Thực Hiện

### 1. Kiểm Tra Nginx

**Lệnh thực thi:**
```bash
nginx -v 2>&1 || echo "Nginx chưa được cài đặt"
```

**Kết quả:**
- Nginx chưa được cài đặt trên hệ thống
- Hệ thống gợi ý: `sudo apt install nginx`

---

### 2. Cập Nhật Package List

**Lệnh thực thi:**
```bash
sudo apt update
```

**Kết quả:**
- ✅ Cập nhật thành công
- Fetched 4,354 kB in 2s (2,071 kB/s)
- 82 packages có thể nâng cấp

---

### 3. Cài Đặt Nginx

**Lệnh thực thi:**
```bash
sudo apt install nginx -y
```

**Kết quả:**
- ✅ Cài đặt thành công nginx và nginx-common
- **Version**: nginx 1.24.0-2ubuntu7.5
- Dung lượng: 564 kB archives, 1,596 kB disk space
- Source: http://vn.archive.ubuntu.com/ubuntu

**Packages đã cài:**
- `nginx` (main package)
- `nginx-common` (common files)

---

### 4. Kiểm Tra Trạng Thái Nginx

**Lệnh thực thi:**
```bash
systemctl status nginx
```

**Kết quả:**
```
● nginx.service - A high performance web server and a reverse proxy server
   Loaded: loaded (/usr/lib/systemd/system/nginx.service; enabled; preset: enabled)
   Active: active (running) since Thu 2025-11-27 08:58:03 +07
   Main PID: 2077149 (nginx)
   Tasks: 9 (limit: 18693)
   Memory: 6.4M (peak: 14.5M)
```

**Thông tin:**
- ✅ Service đang chạy (active)
- ✅ Đã enable auto-start
- 1 master process + 8 worker processes
- Memory usage: 6.4M

---

### 5. Backup Cấu Hình Cũ

**Lệnh thực thi:**
```bash
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
```

**Kết quả:**
- ✅ Đã backup file default config

---

### 6. Copy File Cấu Hình Mới

**Lệnh thực thi:**
```bash
sudo cp /home/dat/PycharmProjects/edge_demo/server_test_reciver/nginx.conf \
    /etc/nginx/sites-available/staging.vandat.io.vn
```

**Kết quả:**
- ✅ File cấu hình đã copy thành công
- Location: `/etc/nginx/sites-available/staging.vandat.io.vn`

**Nội dung cấu hình:**
- Frontend serving từ `/home/dat/PycharmProjects/edge_demo/server_test_reciver`
- WebSocket proxy: `/ws` → `http://127.0.0.1:8800`
- HTTP API proxy: `/api` → `http://127.0.0.1:8800`
- gRPC proxy: `/grpc` → `grpc://127.0.0.1:50051`

---

### 7. Enable Site

**Lệnh thực thi:**
```bash
sudo ln -s /etc/nginx/sites-available/staging.vandat.io.vn \
    /etc/nginx/sites-enabled/staging.vandat.io.vn
```

**Kết quả:**
- ✅ Symbolic link đã tạo thành công

**Xác nhận:**
```bash
ls -la /etc/nginx/sites-enabled/
```

**Output:**
```
lrwxrwxrwx 1 root root 47 Nov 27 08:58 staging.vandat.io.vn -> /etc/nginx/sites-available/staging.vandat.io.vn
lrwxrwxrwx 1 root root 34 Nov 27 08:58 default -> /etc/nginx/sites-available/default
```

---

### 8. Phân Quyền Thư Mục Frontend

**Lệnh thực thi:**
```bash
# Phân quyền thư mục
sudo chmod 755 /home/dat \
              /home/dat/PycharmProjects \
              /home/dat/PycharmProjects/edge_demo \
              /home/dat/PycharmProjects/edge_demo/server_test_reciver

# Phân quyền file HTML
sudo chmod 644 /home/dat/PycharmProjects/edge_demo/server_test_reciver/index.html
```

**Kết quả:**
- ✅ Nginx có quyền đọc thư mục và file
- Permissions: 755 cho folders, 644 cho index.html

---

### 9. Test Cấu Hình

**Lệnh thực thi:**
```bash
sudo nginx -t
```

**Kết quả:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

**Status:** ✅ Cấu hình hợp lệ

---

### 10. Reload Nginx

**Lệnh thực thi:**
```bash
sudo systemctl reload nginx
```

**Kết quả:**
- ✅ Reload thành công (không có downtime)
- Configuration mới đã được apply

---

### 11. Kiểm Tra Auto-Start

**Lệnh thực thi:**
```bash
systemctl is-enabled nginx
```

**Kết quả:**
```
enabled
```

**Status:** ✅ Nginx sẽ tự động start khi server reboot

---

### 12. Test HTTP Connection

**Lệnh thực thi:**
```bash
curl -I http://localhost
```

**Kết quả:**
```
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)
Date: Thu, 27 Nov 2025 01:59:31 GMT
Content-Type: text/html
Content-Length: 615
```

**Status:** ✅ Nginx đang phục vụ HTTP requests

---

### 13. Kiểm Tra Logs

**Lệnh thực thi:**
```bash
sudo tail -20 /var/log/nginx/error.log
```

**Kết quả:**
```
2025/11/27 08:58:04 [notice] 2077149#2077149: using inherited sockets from "5;6;"
```

**Status:** ✅ Không có error, chỉ có notice logs

---

## 📝 Files Đã Tạo/Chỉnh Sửa

### Files mới tạo:
1. `nginx.conf` - File cấu hình nginx gốc cho project

2. `/etc/nginx/sites-available/staging.vandat.io.vn` - Copy của nginx.conf trong hệ thống

3. `/etc/nginx/sites-enabled/staging.vandat.io.vn` - Symbolic link để enable site

4. `/etc/nginx/sites-available/default.backup` - Backup của cấu hình default

---

## 🔧 Cấu Hình Hiện Tại

### Nginx Version
- nginx/1.24.0 (Ubuntu)

### Process Info
- Main PID: 2077149
- Worker processes: 8
- Memory usage: 6.4M

### Sites Enabled
1. `default` (default nginx welcome page)
2. `staging.vandat.io.vn` (project của bạn)

### Port Mapping
- HTTP: Port 80
- HTTPS: Port 443 (chưa cấu hình SSL)

### Proxy Configuration
- WebSocket: `/ws` → `localhost:8800`
- API: `/api` → `localhost:8800`
- gRPC: `/grpc` → `localhost:50051`
- Frontend: `/` → static files từ project directory

---

## ⚠️ Lưu Ý Quan Trọng

> [!IMPORTANT]
> Nginx đã được cấu hình nhưng CHƯA thể truy cập từ domain `staging.vandat.io.vn` vì:
> 1. **DNS chưa được cấu hình** - Cần trỏ domain về IP server
> 2. **SSL chưa được cài đặt** - Nên cài SSL cho bảo mật và WebSocket hoạt động tốt hơn

---

## 🚀 Các Bước Tiếp Theo (Bạn Cần Làm)

### Bước 1: Cấu Hình DNS (BẮT BUỘC)

Đăng nhập vào nhà cung cấp domain và tạo DNS record:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | staging | IP_SERVER_CỦA_BẠN | 3600 |

**Ví dụ:** 
- Nếu IP server là `123.456.789.10`
- Tạo A record: `staging.vandat` → `123.456.789.10`

**Kiểm tra DNS:**
```bash
nslookup staging.vandat.io.vn
# hoặc
dig staging.vandat.io.vn
```

Chờ 5-15 phút để DNS propagate.

---

### Bước 2: Cài Đặt SSL Certificate (KHUYẾN NGHỊ)

Sau khi DNS đã trỏ đúng:

```bash
# Cài certbot
sudo apt install certbot python3-certbot-nginx -y

# Tự động cài SSL
sudo certbot --nginx -d staging.vandat.io.vn

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Bước 3: Update Frontend URL

Sau khi có SSL, update file `index.html`:

**Thay đổi dòng 13:**
```html
<!-- Cũ -->
<input id="ws-url" size="40" value="ws://localhost:8800/ws">

<!-- Mới -->
<input id="ws-url" size="40" value="wss://staging.vandat.io.vn/ws">
```

---

### Bước 4: Uncomment SSL Config trong Nginx

Sau khi có SSL certificate, chỉnh sửa `/etc/nginx/sites-available/staging.vandat.io.vn`:

1. Uncomment dòng redirect HTTP → HTTPS (dòng 5)
2. Uncomment toàn bộ server block port 443 (dòng 7-14)
3. Reload nginx: `sudo systemctl reload nginx`

---

## 🧪 Testing Sau Khi Hoàn Thành DNS + SSL

### Test Frontend
```bash
curl https://staging.vandat.io.vn
```

### Test WebSocket (Browser Console)
```javascript
const ws = new WebSocket('wss://staging.vandat.io.vn/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
```

### Test API
```bash
curl https://staging.vandat.io.vn/api/
```

---

## 📊 Monitoring Commands

### Kiểm tra nginx status
```bash
sudo systemctl status nginx
```

### Xem logs realtime
```bash
# Error log
sudo tail -f /var/log/nginx/staging.vandat.io.vn.error.log

# Access log  
sudo tail -f /var/log/nginx/staging.vandat.io.vn.access.log
```

### Kiểm tra ports đang listen
```bash
sudo ss -tulnp | grep nginx
```

### Test cấu hình trước khi reload
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🐛 Troubleshooting

### Nếu gặp 502 Bad Gateway
1. Kiểm tra FastAPI đang chạy: `curl http://localhost:8800`
2. Xem logs: `sudo tail -f /var/log/nginx/error.log`
3. Kiểm tra port 8800 và 50051 đang listen

### Nếu gặp 404 Not Found cho index.html
1. Kiểm tra permissions: `ls -la /home/dat/PycharmProjects/edge_demo/server_test_reciver/index.html`
2. Kiểm tra nginx có quyền đọc: `sudo -u www-data cat /home/dat/.../index.html`

### Nếu WebSocket không kết nối được
1. Kiểm tra browser console có lỗi gì
2. Kiểm tra nginx error log
3. Đảm bảo dùng `wss://` (not `ws://`) khi có SSL

---

## ✅ Checklist Hoàn Thành

- [x] Cài đặt nginx
- [x] Cấu hình nginx cho domain
- [x] Phân quyền files
- [x] Test cấu hình
- [x] Reload nginx
- [x] Verify service đang chạy
- [ ] **CẦN LÀM**: Cấu hình DNS
- [ ] **CẦN LÀM**: Cài đặt SSL certificate
- [ ] **CẦN LÀM**: Update index.html với URL mới

---

## 📚 Files Project

- `main.py` - FastAPI application với WebSocket và gRPC
- `index.html` - Frontend để test WebSocket connection
- `nginx.conf` - Cấu hình nginx cho domain
- `frame.proto` - gRPC protocol definition
- `frame_pb2.py` - Generated gRPC code
- `frame_pb2_grpc.py` - Generated gRPC servicer code
