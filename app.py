if __name__ == "__main__":
    urls = [
        "https://www.reddit.com/u/hollandashly",
        "https://www.instagram.com/some_private_account/",
        "https://www.youtube.com/@suspendedchannel",
    ]

    for url in urls:
        result = check_account_status(url)
        print(f"{url} → {result}")
