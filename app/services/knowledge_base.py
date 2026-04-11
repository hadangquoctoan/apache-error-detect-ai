# Apache Error Knowledge Base
# Chứa các lỗi phổ biến của Apache, nguyên nhân và cách khắc phục
from typing import List, Dict, Optional

APACHE_ERROR_KB = [
    {
        "error_code": "AH00124",
        "title": "Request exceeded the limit of internal redirects",
        "content": """## Lỗi AH00124: Request exceeded the limit of internal redirects

### Mô tả
Request đã vượt quá số lượng internal redirects tối đa (10 lần). Điều này thường do vòng lặp redirect vô hạn.

### Nguyên nhân phổ biến
1. **RewriteRule loop**: Các rule viết sai tạo ra vòng lặp redirect
2. **.htaccess conflict**: Xung đột giữa các rewrite rules
3. **PHP framework redirect**: Framework như Laravel, CodeIgniter redirect sai
4. **SSL/HTTPS redirect loop**: Redirect HTTP ↔ HTTPS không đúng

### Cách khắc phục
1. Kiểm tra file .htaccess và Apache config
2. Thêm điều kiện dừng: `RewriteCond %{ENV:REDIRECT_STATUS} !^$`
3. Kiểm tra RewriteRule pattern không match với destination
4. Với SSL loop, đảm bảo chỉ redirect một chiều

### Ví dụ fix
```apache
# Trong .htaccess
RewriteEngine On
RewriteCond %{ENV:REDIRECT_STATUS} !^$
RewriteRule ^ - [L]

RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```""",
        "severity": "HIGH",
        "category": "redirect_loop"
    },
    {
        "error_code": "AH00130",
        "title": "Handler for (null) returned invalid result",
        "content": """## Lỗi AH00130: Handler for (null) returned invalid result

### Mô tả
Apache không thể xử lý request vì handler trả về kết quả không hợp lệ.

### Nguyên nhân phổ biến
1. **Missing PHP handler**: PHP module không được load
2. **Handler mismatch**: Cấu hình handler không đúng với file type
3. **Corrupted module**: Module Apache bị hỏng
4. **Missing file**: File được request không tồn tại

### Cách khắc phục
1. Kiểm tra PHP module có được enable:
   ```bash
   a2enmod php8.1
   apachectl -M | grep php
   ```

2. Kiểm tra AddHandler trong config:
   ```apache
   <FilesMatch \\.php$>
       SetHandler application/x-httpd-php
   </FilesMatch>
   ```

3. Restart Apache:
   ```bash
   systemctl restart apache2
   ```

4. Kiểm tra error log chi tiết hơn""",
        "severity": "MEDIUM",
        "category": "handler_error"
    },
    {
        "error_code": "AH00072",
        "title": "make_sock: could not bind to address",
        "content": """## Lỗi AH00072: make_sock: could not bind to address

### Mô tả
Apache không thể bind vào IP/port được chỉ định. Thường là port 80 hoặc 443.

### Nguyên nhân phổ biến
1. **Port bị chiếm**: Service khác đang dùng port đó (nginx, IIS, another Apache)
2. **Permission denied**: Apache không có quyền bind vào privileged port (<1024)
3. **IPv6/IPv4 conflict**: Cấu hình listen sai
4. **Multiple Listen directives**: Cùng một port được khai báo nhiều lần

### Cách khắc phục
1. Kiểm tra port 80/443 có đang bị chiếm không:
   ```bash
   # Linux
   lsof -i :80
   netstat -tlnp | grep :80
   
   # Windows
   netstat -ano | findstr :80
   ```

2. Nếu port bị chiếm, stop service đó hoặc đổi port Apache:
   ```apache
   Listen 8080
   ```

3. Với privileged port, chạy Apache với root hoặc dùng:
   ```bash
   setcap 'cap_net_bind_service=+ep' /usr/sbin/apache2
   ```

4. Kiểm tra Apache config không có Listen trùng lặp""",
        "severity": "CRITICAL",
        "category": "startup_error"
    },
    {
        "error_code": "AH02429",
        "title": "Response header name contains invalid characters",
        "content": """## Lỗi AH02429: Response header name contains invalid characters

### Mô tả
Apache từ chối response header vì tên header chứa ký tự không hợp lệ.

### Nguyên nhân phổ biến
1. **PHP header output**: PHP script output header lỗi
2. **Application bug**: Ứng dụng web sinh ra header sai format
3. **Middleware issue**: Reverse proxy thêm header không hợp lệ

### Cách khắc phục
1. Kiểm tra PHP/application output headers
2. Thêm header sanitize trong Apache:
   ```apache
   RequestHeader unset X-Custom-Header
   ```

3. Kiểm tra application code:
   ```php
   // PHP - kiểm tra header trước khi output
   header("Content-Type: text/html; charset=utf-8");
   ```""",
        "severity": "MEDIUM",
        "category": "header_error"
    },
    {
        "error_code": "AH01630",
        "title": "client denied by server configuration",
        "content": """## Lỗi AH01630: client denied by server configuration

### Mô tả
Client bị từ chối truy cập do cấu hình Apache.

### Nguyên nhân phổ biến
1. **Require directive**: Cấu hình `<Require>` không cho phép
2. **IP whitelist/blacklist**: Deny from all hoặc IP restriction
3. **.htaccess block**: File .htaccess chặn quyền truy cập

### Cách khắc phục
1. Kiểm tra Apache config:
   ```apache
   # Cho phép tất cả
   <RequireAll>
       Require all granted
   </RequireAll>
   
   # Hoặc chỉ cho phép IP cụ thể
   <RequireAny>
       Require ip 192.168.1.0/24
   </RequireAny>
   ```

2. Kiểm tra .htaccess
3. Kiểm tra error log để biết IP nào bị chặn""",
        "severity": "LOW",
        "category": "access_denied"
    },
    {
        "error_code": "AH00112",
        "title": "PID file not created",
        "content": """## Lỗi AH00112: PID file not created

### Mô tả
Apache không thể tạo PID file khi khởi động.

### Nguyên nhân phổ biến
1. **Permission issue**: Không có quyền ghi vào thư mục logs/
2. **Disk full**: Ổ đĩa đầy
3. **Lock file conflict**: Apache process cũ chưa được stop
4. **Config error**: PidFile directive trỏ đến đường dẫn không tồn tại

### Cách khắc phục
1. Kiểm tra quyền thư mục:
   ```bash
   chown -R www-data:www-data /var/run/apache2
   chmod 755 /var/run/apache2
   ```

2. Kill Apache process cũ:
   ```bash
   pkill apache2
   # hoặc
   killall apache2
   ```

3. Kiểm tra disk space:
   ```bash
   df -h
   ```

4. Kiểm tra PidFile directive""",
        "severity": "HIGH",
        "category": "startup_error"
    },
    {
        "error_code": "AH00526",
        "title": "Syntax error",
        "content": """## Lỗi AH00526: Syntax error

### Mô tả
Apache config có syntax error.

### Nguyên nhân phổ biến
1. **Missing closing tag**: Thiếu `>` hoặc `</Directory>`
2. **Typo**: Lỗi chính tả trong directive
3. **Quote mismatch**: Thiếu dấu `"` hoặc `'`
4. **Invalid value**: Giá trị không hợp lệ

### Cách khắc phục
1. Kiểm tra syntax trước khi restart:
   ```bash
   apachectl configtest
   # hoặc
   apache2ctl configtest
   ```

2. Dùng Apache config diagnostic:
   ```bash
   httpd -t
   ```

3. Kiểm tra dòng được chỉ ra trong error message""",
        "severity": "CRITICAL",
        "category": "config_error"
    },
    {
        "error_code": "AH00087",
        "title": "Could not open password file",
        "content": """## Lỗi AH00087: Could not open password file

### Mô tả
Apache không thể mở file password cho Basic Auth hoặc Digest Auth.

### Nguyên nhân phổ biến
1. **File not found**: Đường dẫn trong AuthUserFile sai
2. **Permission denied**: Apache không đọc được file
3. **File corrupted**: File password bị hỏng
4. **Wrong format**: File không đúng format htpasswd

### Cách khắc phục
1. Tạo/kiểm tra file password:
   ```bash
   htpasswd -c /etc/apache2/.htpasswd username
   ```

2. Set quyền đúng:
   ```bash
   chown www-data:www-data /etc/apache2/.htpasswd
   chmod 640 /etc/apache2/.htpasswd
   ```

3. Kiểm tra đường dẫn trong config:
   ```apache
   AuthUserFile /full/path/to/.htpasswd
   ```""",
        "severity": "MEDIUM",
        "category": "auth_error"
    },
    {
        "error_code": "AH01873",
        "title": "Init: Unable to correct temporary directory",
        "content": """## Lỗi AH01873: Init: Unable to correct temporary directory

### Mô tả
Apache không thể access temporary directory.

### Nguyên nhân phổ biến
1. **Temp dir missing**: /tmp không tồn tại hoặc không có quyền
2. **Disk full**: Không gian tmp đầy
3. **Security module**: SELinux/AppArmor chặn access

### Cách khắc phục
1. Kiểm tra /tmp:
   ```bash
   ls -la /tmp
   chmod 1777 /tmp
   ```

2. Với SELinux:
   ```bash
   chcon -R system_u:object_r:tmp_t:s0 /tmp
   ```

3. Set TempDir trong Apache:
   ```apache
   CoreDumpDirectory /var/cache/apache2
   ```""",
        "severity": "MEDIUM",
        "category": "startup_error"
    },
    {
        "error_code": "AH00189",
        "title": "Invalid ErrorLog directive",
        "content": """## Lỗi AH00189: Invalid ErrorLog directive

### Mô tả
ErrorLog directive trong Apache config không hợp lệ.

### Nguyên nhân phổ biến
1. **Path not exist**: Đường dẫn log không tồn tại
2. **Permission denied**: Không có quyền ghi vào file/log directory
3. **Syntax error**: Cú pháp ErrorLog sai

### Cách khắc phục
1. Tạo log directory:
   ```bash
   mkdir -p /var/log/apache2
   chown -R www-data:www-data /var/log/apache2
   ```

2. Tạo error log file:
   ```bash
   touch /var/log/apache2/error.log
   chmod 644 /var/log/apache2/error.log
   ```

3. Kiểm tra config:
   ```apache
   ErrorLog /var/log/apache2/error.log
   ```""",
        "severity": "MEDIUM",
        "category": "config_error"
    },
    {
        "error_code": "500",
        "title": "Internal Server Error (HTTP 500)",
        "content": """## Lỗi 500: Internal Server Error

### Mô tả
Server gặp lỗi không xác định khi xử lý request.

### Nguyên nhân phổ biến
1. **PHP Error**: Lỗi PHP code (syntax error, undefined function)
2. **Permission**: File/folder permission sai
3. **htaccess error**: RewriteRule lỗi hoặc directive không hỗ trợ
4. **Timeout**: Script chạy quá lâu
5. **Memory limit**: PHP memory_limit exceeded

### Cách khắc phục
1. Bật display_errors trong php.ini:
   ```php
   display_errors = On
   error_reporting = E_ALL
   ```

2. Kiểm tra error_log của PHP

3. Kiểm tra permissions:
   ```bash
   # Files: 644
   find /var/www -type f -exec chmod 644 {} \\;
   # Directories: 755
   find /var/www -type d -exec chmod 755 {} \\;
   ```

4. Tăng PHP limits:
   ```php
   max_execution_time = 300
   memory_limit = 256M
   ```""",
        "severity": "HIGH",
        "category": "http_error"
    },
    {
        "error_code": "502",
        "title": "Bad Gateway (HTTP 502)",
        "content": """## Lỗi 502: Bad Gateway

### Mô tả
Apache làm reverse proxy nhận được response không hợp lệ từ upstream server.

### Nguyên nhân phổ biến
1. **Backend down**: Upstream server (Node, Python, PHP-FPM) không chạy
2. **Backend timeout**: Upstream phản hồi quá chậm
3. **Protocol mismatch**: HTTP version không tương thích
4. **Overload**: Upstream bị quá tải

### Cách khắc phục
1. Kiểm tra upstream service:
   ```bash
   # PHP-FPM
   systemctl status php-fpm
   # Node
   pm2 status
   ```

2. Kiểm tra logs:
   ```bash
   tail -f /var/log/apache2/error.log
   tail -f /var/log/php-fpm/www-error.log
   ```

3. Tăng timeout:
   ```apache
   ProxyTimeout 300
   ```

4. Restart upstream service""",
        "severity": "HIGH",
        "category": "http_error"
    },
    {
        "error_code": "503",
        "title": "Service Unavailable (HTTP 503)",
        "content": """## Lỗi 503: Service Unavailable

### Mô tả
Server tạm thời không thể xử lý request (overloaded hoặc maintenance).

### Nguyên nhân phổ biến
1. **Server overloaded**: Quá nhiều request
2. **Maintenance**: Server đang bảo trì
3. **Backend unavailable**: Upstream services down
4. **Rate limiting**: Quá nhiều request từ 1 IP

### Cách khắc phục
1. Kiểm tra server load:
   ```bash
   top
   htop
   df -h
   ```

2. Kiểm tra connection limits trong Apache:
   ```apache
   ServerLimit 256
   MaxRequestWorkers 256
   ```

3. Enable status monitoring:
   ```apache
   <Location /server-status>
       SetHandler server-status
       Require ip 192.168.1.0/24
   </Location>
   ```

4. Kiểm tra fail2ban/logstatsd""",
        "severity": "HIGH",
        "category": "http_error"
    },
    {
        "error_code": "403",
        "title": "Forbidden (HTTP 403)",
        "content": """## Lỗi 403: Forbidden

### Mô tả
Server từ chối truy cập resource.

### Nguyên nhân phổ biến
1. **Permission**: File/folder permission không cho phép đọc
2. **Directory listing**: Không có index file và DirectoryIndex bị disable
3. **htaccess deny**: .htaccess chặn truy cập
4. **SELinux**: SELinux policy ngăn truy cập

### Cách khắc phục
1. Kiểm tra permissions:
   ```bash
   ls -la /var/www/html/
   chmod 755 /var/www/html
   chmod 644 /var/www/html/*.php
   ```

2. Tạo index file:
   ```bash
   echo "<?php phpinfo(); ?>" > /var/www/html/index.php
   ```

3. Kiểm tra .htaccess:
   ```apache
   Require all granted
   ```

4. Với SELinux:
   ```bash
   chcon -R -t httpd_sys_content_t /var/www/html
   ```""",
        "severity": "MEDIUM",
        "category": "http_error"
    },
    {
        "error_code": "404",
        "title": "Not Found (HTTP 404)",
        "content": """## Lỗi 404: Not Found

### Mô tả
Resource được request không tồn tại trên server.

### Nguyên nhân phổ biến
1. **URL typo**: Đường dẫn URL sai
2. **Missing file**: File đã bị xóa hoặc di chuyển
3. **htaccess rewrite**: RewriteRule chuyển hướng sai
4. **Case sensitive**: Linux phân biệt hoa thường

### Cách khắc phục
1. Kiểm tra file tồn tại:
   ```bash
   ls -la /var/www/html/
   ```

2. Kiểm tra DocumentRoot:
   ```apache
   DocumentRoot "/var/www/html"
   ```

3. Enable mod_rewrite và kiểm tra .htaccess

4. Thêm custom 404 page:
   ```apache
   ErrorDocument 404 /404.html
   ```""",
        "severity": "LOW",
        "category": "http_error"
    }
]


def get_apache_error_kb() -> List[Dict]:
    """
    Lấy toàn bộ Apache Error Knowledge Base

    Returns:
        List of dict với error_code, title, content, severity, category
    """
    return APACHE_ERROR_KB


def get_errors_by_code(error_code: str) -> Optional[Dict]:
    """Lấy thông tin lỗi theo mã"""
    for error in APACHE_ERROR_KB:
        if error["error_code"] == error_code:
            return error
    return None


def get_errors_by_severity(severity: str) -> List[Dict]:
    """Lấy các lỗi theo mức độ nghiêm trọng"""
    return [e for e in APACHE_ERROR_KB if e["severity"] == severity]


def get_errors_by_category(category: str) -> List[Dict]:
    """Lấy các lỗi theo category"""
    return [e for e in APACHE_ERROR_KB if e["category"] == category]


def prepare_kb_for_embedding() -> List[Dict]:
    """
    Chuẩn bị KB data để embed vào vector store
    Mỗi document gồm: content, source, metadata
    """
    documents = []
    for error in APACHE_ERROR_KB:
        doc = {
            "content": f"""Error Code: {error['error_code']}
Title: {error['title']}
Severity: {error['severity']}
Category: {error['category']}

{error['content']}""",
            "source": f"apache_error_{error['error_code']}",
            "metadata": {
                "error_code": error["error_code"],
                "title": error["title"],
                "severity": error["severity"],
                "category": error["category"]
            }
        }
        documents.append(doc)

    return documents
