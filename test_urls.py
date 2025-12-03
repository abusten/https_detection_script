import requests
import concurrent.futures
import time
import os


def _format_status(code, error_msg, extra_note=""):
    if code is not None:
        base = f"状态码 {code}"
    elif error_msg:
        base = f"错误: {error_msg}"
    else:
        base = "无响应"

    if extra_note:
        return f"{base} ({extra_note})"
    return base


def check_url(domain: str):
    """检测单个域名并返回分类结果。"""
    domain = domain.strip()
    if not domain:
        return None

    https_url = f"https://{domain}"
    http_url = f"http://{domain}"

    https_works = False
    http_works = False
    https_code = None
    http_code = None
    https_error = ""
    http_error = ""
    http_note = ""

    try:
        response_https = requests.get(https_url, timeout=10, allow_redirects=True)
        https_code = response_https.status_code
        if response_https.status_code < 500:
            https_works = True
    except requests.exceptions.RequestException as exc:
        https_error = str(exc)

    try:
        response_http = requests.get(http_url, timeout=10, allow_redirects=False)
        http_code = response_http.status_code
        if response_http.status_code < 500:
            redirect_location = response_http.headers.get('Location', '')
            if response_http.is_redirect and redirect_location.startswith('https'):
                http_note = f"重定向到 {redirect_location}"
                http_works = False
            else:
                http_works = True
        else:
            http_note = "返回 5xx"
    except requests.exceptions.RequestException as exc:
        http_error = str(exc)

    https_status = _format_status(https_code, https_error)
    http_status = _format_status(http_code, http_error, http_note)

    if https_works and not http_works:
        category = "normal"
    elif not https_works:
        category = "https_fail"
    elif http_works:
        category = "http_accessible"
    else:
        category = "other"

    message = f"{domain}\tHTTPS: {https_status} | HTTP: {http_status}"
    return {
        "domain": domain,
        "category": category,
        "message": message
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, 'url.txt')

    try:
        with open(input_path, 'r', encoding='utf-8') as src:
            domains = []
            for line in src:
                parts = [item.strip() for item in line.split(',')]
                domains.extend([item for item in parts if item])
    except FileNotFoundError:
        print(f"错误：在 {script_dir} 下找不到 url.txt")
        return

    if not domains:
        print("url.txt 为空，没有可测试的域名。")
        return

    output_dir = os.path.join(script_dir, "results")
    os.makedirs(output_dir, exist_ok=True)

    category_files = {
        "normal": os.path.join(output_dir, "normal_https_only.txt"),
        "https_fail": os.path.join(output_dir, "abnormal_https_failed.txt"),
        "http_accessible": os.path.join(output_dir, "abnormal_http_accessible.txt"),
        "other": os.path.join(output_dir, "abnormal_other.txt"),
    }
    aggregated = {key: [] for key in category_files}
    error_records = []

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_domain = {executor.submit(check_url, domain): domain for domain in domains}
        for future in concurrent.futures.as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                if result:
                    aggregated[result["category"]].append(result["message"])
            except Exception as exc:
                error_records.append(f"{domain}\t意外错误: {exc}")

    for category, path in category_files.items():
        lines = aggregated.get(category, [])
        with open(path, 'w', encoding='utf-8') as dest:
            if lines:
                dest.write("\n".join(lines))

    error_file = None
    if error_records:
        error_file = os.path.join(output_dir, "abnormal_unexpected_errors.txt")
        with open(error_file, 'w', encoding='utf-8') as dest:
            dest.write("\n".join(error_records))

    elapsed = time.time() - start_time

    summary = [
        f"总计 {len(domains)} 个域名，耗时 {elapsed:.2f} 秒。",
        "输出文件：",
        *[f"- {category}: {path}" for category, path in category_files.items()],
    ]
    if error_file:
        summary.append(f"- unexpected_errors: {error_file}")

    print("\n".join(summary))

if __name__ == "__main__":
    main()
