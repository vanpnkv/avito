import re
from typing import List, Dict, Any

import pandas as pd

class Parser:
    def __init__(self):
        self.ob_snapshot_pattern = '(\d{2}-\d{2}-\d{2} \d+:\d+:\d+.\d+).+(\d{16}).+bid_size: (\d+).+ask_size: (\d+)'
        self.ob_depth_pattern = 'price: (\d+.\d+).+volume: (\d+)'
    
    def parse(self, file_path: str, chunk_size: int) -> List[Dict[str, Any]]:
        result = []
        current_data = {}
        flag = 0
        ask_price = ask_volume = bid_price = bid_volume = 0
        max_bid_price = max_bid_volume = total_bid_volume = 0
        min_ask_price = min_ask_volume = total_ask_volume = 0
        
        with open(file_path, 'r') as file:
            while True:
                chunk = file.readlines(chunk_size)
                if not chunk:
                    break
                
                for line in chunk:
                    if 'OrderbookSnapshot' in line:
                        if flag:
                            current_data = {'receive_time': receive_time, 'server_time': int(server_time), 
                                            'bid_size': int(bid_size), 'max_bid_price': float(max_bid_price), 
                                            'max_bid_volume': int(max_bid_volume), 'total_bid_volume': int(total_bid_volume),
                                            'ask_size': int(ask_size), 'min_ask_price': float(min_ask_price), 
                                            'min_ask_volume': int(min_ask_volume), 'total_ask_volume': int(total_ask_volume)}
                            result.append(current_data)
                            current_data = {}
                            ask_price = ask_volume = bid_price = bid_volume = 0
                            max_bid_price = max_bid_volume = total_bid_volume = 0
                            min_ask_price = min_ask_volume = total_ask_volume = 0
                            flag = 0
                            
                        receive_time, server_time, bid_size, ask_size = (re.findall(self.ob_snapshot_pattern, line)[0])
                        flag = 1 # TODO: refactor flag
                    elif line.startswith('Ask'):
                        ask_price , ask_volume = re.findall(self.ob_depth_pattern, line)[0]
                        ask_volume = int(ask_volume)
                        total_ask_volume += ask_volume
                        
                        if min_ask_price == 0 or ask_price < min_ask_price:
                            min_ask_price = ask_price
                            min_ask_volume = ask_volume
                    elif line.startswith('Bid'):
                        bid_price , bid_volume = re.findall('price: (\d+.\d+).+volume: (\d+)', line)[0]
                        bid_volume = int(bid_volume)
                        total_bid_volume += bid_volume
                        
                        if max_bid_price == 0 or bid_price > max_bid_price:
                            max_bid_price = bid_price
                            max_bid_volume = bid_volume

                    else:
                        continue
                        
            return result
