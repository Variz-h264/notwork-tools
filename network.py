import socket
import psutil
import speedtest
import requests
import subprocess
import time
import os

def get_ip_addresses():
    ip_addresses = []

    # Get all network interfaces
    interfaces = psutil.net_if_addrs()
    for interface_name, interface_addresses in interfaces.items():
        for address in interface_addresses:
            # Check for IPv4 address and skip loopback and link-local addresses
            if address.family == socket.AF_INET and not address.address.startswith(('127.', '169.254.')):
                ip_addresses.append((interface_name, address.address))

    return ip_addresses

def check_internet_connection():
    try:
        # Attempt to connect to a well-known internet host (Cloudflare DNS)
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass
    return False

def check_proxy_usage():
    try:
        # Make a request to a URL that shows your IP address
        url = "https://api.ipify.org?format=json"
        response = requests.get(url, timeout=5)

        # Check if the response IP matches your current IP
        if response.ok:
            data = response.json()
            if data.get("ip"):
                return False  # No proxy detected
            else:
                return True   # Proxy detected
        else:
            return False      # Unable to determine

    except requests.RequestException:
        return False          # Request failed

def test_internet_speed():
    print("Running speed test...")  # Print status message

    st = speedtest.Speedtest()
    st.get_best_server()

    start_time = time.time()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    end_time = time.time()
    download_time = end_time - start_time

    start_time = time.time()
    upload_speed = st.upload() / 1_000_000     # Convert to Mbps
    end_time = time.time()
    upload_time = end_time - start_time

    return download_speed, upload_speed, download_time, upload_time

def get_ping():
    try:
        # Ping Cloudflare DNS (1.1.1.1) and get average ping time
        ping_response = subprocess.Popen(["ping", "-c", "3", "1.1.1.1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, error = ping_response.communicate()
        if ping_response.returncode == 0:
            lines = out.decode('utf-8').splitlines()
            avg_time = lines[-1].split('/')[-3]  # Extracting average ping time (ms) from ping output
            return avg_time
        else:
            return "Failed to ping"
    except Exception as e:
        print(f"Exception occurred while pinging: {e}")
        return "Failed to ping"
    
def get_isp_info():
    try:
        # Use speedtest-cli to get ISP information
        st = speedtest.Speedtest()
        st.get_best_server()

        isp = st.get_best_server()['host']
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000     # Convert to Mbps

        return isp, download_speed, upload_speed
    except Exception as e:
        print(f"Exception occurred while getting ISP info: {e}")
        return "Unknown", 0.0, 0.0
    
if __name__ == "__main__":
    # Record start time
    overall_start_time = time.time()

    # Check internet connection
    if check_internet_connection():
        print("Connected to the internet.")
    else:
        print("Not connected to the internet.")

    # Get IP addresses
    ip_addresses = get_ip_addresses()
    if ip_addresses:
        print("\nIP addresses:")
        for interface, ip in ip_addresses:
            print(f"- Interface: {interface}, IP: {ip}")
    else:
        print("\nNo IP addresses found.")

    # Check proxy usage
    if check_proxy_usage():
        print("\nProxy detected.")
    else:
        print("\nNo proxy detected.")

    # Get ping to DNS
    ping_time = get_ping()
    print(f"\nPing to Cloudflare DNS (1.1.1.1): {ping_time} ms")

    isp, download_speed, upload_speed = get_isp_info()
    print("\nISP Information:")
    print(f"ISP: {isp}")

    # Test internet speed
    download_speed, upload_speed, download_time, upload_time = test_internet_speed()
    print("\nSpeed test results:")
    print(f"Download Speed: {download_speed:.2f} Mbps")
    print(f"Upload Speed: {upload_speed:.2f} Mbps")

    # Print total time taken
    overall_end_time = time.time()
    overall_time = overall_end_time - overall_start_time
    print(f"\nTotal time taken: {overall_time:.2f} seconds")

    # Pause and wait for user input before closing
    input("\nPress Enter to exit...")