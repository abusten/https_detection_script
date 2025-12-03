# URL 可用性批量校验脚本

该脚本会批量读取 `url.txt` 中的域名，检测它们是否满足“**可以通过 HTTPS 访问但无法通过 HTTP 访问**”的要求，并将结果写入不同的 TXT 文件。

## 环境准备

```bash
pip install -r requirements.txt
```

## 使用方法

1. 在 `url.txt` 中按行填写需要检测的域名（不包含协议头）。
2. 运行脚本：
   ```bash
   python test_urls.py
   ```
3. 查看 `results/` 目录下生成的结果文件：
   - `normal_https_only.txt`：符合要求（HTTPS 正常、HTTP 受限或重定向）的域名。
   - `abnormal_https_failed.txt`：HTTPS 不可访问的域名。
   - `abnormal_http_accessible.txt`：HTTP 仍可直接访问的域名。
   - `abnormal_other.txt`：其他无法归类的异常情况。
   - `abnormal_unexpected_errors.txt`（如存在）：脚本执行过程中出现的意外错误。

> 每条记录都包含详细的 HTTP/HTTPS 状态描述，便于进一步排查。
