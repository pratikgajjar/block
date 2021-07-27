import requests
from requests import exceptions
import json
import os
import hashlib
import pickle
import asyncio
import aiodns
import idna

hosts = set()


os.makedirs('custom', exist_ok=True)


def get_hash(value: str):
    return hashlib.md5(value.encode("utf-8")).hexdigest()


loop = asyncio.get_event_loop()
resolver = aiodns.DNSResolver(loop=loop)


async def query(name, query_type):
    try:
        await resolver.query(name, query_type)
        return name
    except (aiodns.error.DNSError, idna.core.IDNAError):
        return 0


async def check_valid_dns():
    dns_blast = []
    
    for h in hosts:
        dns_blast.append(query(h, 'A'))
    
    print("Gathering Async Bois -", len(dns_blast))
    return await asyncio.gather(*dns_blast)


def download_file(url):
    local_filename = hashlib.md5(url.encode("utf-8")).hexdigest() + ".txt"
    print(url, local_filename)
    # NOTE the stream=True parameter below
    file_path = os.path.join('custom', local_filename)
    if os.path.exists(file_path):
        print("Skipping ...")
        return

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return local_filename


def process_line(line: str):
    if not line:
        return
    if line.startswith("#") or line.startswith("!") or line.startswith("-"):
        return
    host_name = line.split(" ")[-1]
    hosts.add(host_name.strip("\n"))


def read_file(file_name: str):
    print("Host size - ", len(hosts))
    with open(file_name, 'r') as f:
        line = f.readline()
        while line:
            process_line(line)
            line = f.readline()


def gen_hosts_txt(hosts_):
    with open("hosts.txt", "w") as f:
        for h in hosts_:
            if h:
                f.write(f"0.0.0.0 {h}\n")
            

async def main():
    with open('sources.json') as f:
        sources = json.load(f)["sources"]
    links = []
    for li in sources:
        if "block.energized.pro" in li["url"] or li["format"] != "plain":
            continue
        try:
            download_file(li["url"])
        except (exceptions.ConnectionError, exceptions.HTTPError):
            pass

    all_files = os.listdir("custom")

    for f in all_files:
        print("Reading . . .", f)
        read_file(os.path.join("custom", f))


    gen_hosts_txt(hosts)


def dump_object():
    with open('hosts_set', 'wb') as f:
        pickle.dump(hosts, f)


def post_process():
    with open('hosts_set', 'rb') as f:
        p_hosts = pickle.load(f)

    gen_hosts_txt(p_hosts)


if __name__ == '__main__':
    x = loop.run_until_complete(main())
