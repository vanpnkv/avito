import pandas as pd


class NaiveStrategy:
    def __init__(self, deribit_df, deribit_fee, bitmex_df, bitmex_fee, threshold, delay, start_date):
        self.MAX_POSITION = 1e6
        
        self.deribit_df = deribit_df
        self.deribit_fee = deribit_fee
        
        self.bitmex_df = bitmex_df
        self.bitmex_fee = bitmex_fee
        
        self.both_df = pd.merge_asof(self.deribit_df, self.bitmex_df, right_index=True, left_index=True, 
                                     direction='backward', tolerance=pd.Timedelta('5ms'), 
                                     suffixes=['_deribit', '_bitmex'])
        
        self.both_df.dropna(inplace=True)
        
        self.threshold = threshold
        self.delay = delay
        
        self.total_return = 0
        
        self.actual_date = pd.to_datetime(start_date)

    def _make_order(self, current_date, coef, buy_price, buy_real_price, buy_volume, buy_real_volume, buy_fee,
                    sell_price, sell_real_price, sell_volume, sell_real_volume, sell_fee):
        
        print(current_date)
        print(coef)
        corrected_buy_price = (1 - buy_fee) * buy_price
        corrected_sell_price = (1 + sell_fee) * sell_price
        print(f'buy price: {buy_price}')
        print(f'buy corrected price: {corrected_buy_price}')
        print(f'sell price: {sell_price}')
        print(f'sell corrected price: {corrected_sell_price}')
        
        buy_amount = self.MAX_POSITION / corrected_buy_price
        sell_amount = self.MAX_POSITION / corrected_sell_price
        
        if buy_amount >= buy_volume:
            buy_amount = buy_volume * 0.95
            sell_amount = buy_amount (1 - coef)
        elif sell_amount >= sell_volume:
            sell_amount = sell_volume * 0.95
            buy_amount = sell_amount * (1 + coef)
                
        if ((buy_price == buy_real_price) and (buy_real_volume >= buy_amount) and 
            (sell_price == sell_real_price) and (sell_real_volume >= sell_amount)):

            self.total_return += (1 - buy_fee) * buy_amount / buy_price - (1 + sell_fee) * sell_amount / sell_price
            
            print(f'Buy {buy_amount} BTC with corrected price {corrected_buy_price}$, total_position: {buy_amount*corrected_buy_price}')
            print(f'Sell {sell_amount} BTC with corrected price {corrected_sell_price}$, total_position: {sell_amount*corrected_sell_price}')
            print(f'total_return = {self.total_return}')
            return True
            
        else:
            print('You loose, go next')
            return False
            
    def run(self):
        for row in self.both_df.itertuples():
            current_date = row.Index
            if current_date > self.actual_date:
                self.actual_date = current_date + pd.Timedelta(self.delay)
                
                buy_bitmex_coef = 1 - ((1 - self.bitmex_fee) * row.min_ask_price_bitmex / ((1 + self.deribit_fee) * row.max_bid_price_deribit))
                buy_deribit_coef = 1 - ((1 - self.deribit_fee) * row.min_ask_price_deribit / ((1 + self.bitmex_fee) * row.max_bid_price_bitmex))
    
                if  (buy_bitmex_coef > self.threshold) and (buy_bitmex_coef > buy_deribit_coef):
                    # buy on bitmex, sell on deribit
                    
                    i = self.both_df.index.searchsorted(self.actual_date)
                    if i >= self.both_df.shape[0]:
                        break
                    print('Bitmex buy')
                    buy_real_price, buy_real_volume = self.both_df.iloc[i][['min_ask_price_bitmex', 'min_ask_volume_bitmex']].values
                    sell_real_price, sell_real_volume = self.both_df.iloc[i][['max_bid_price_deribit', 'max_bid_volume_deribit']].values
                    
                    self._make_order(current_date=current_date,
                                                             coef=buy_bitmex_coef,
                                     buy_price=row.min_ask_price_bitmex,
                                     buy_real_price=buy_real_price, 
                                     buy_volume=row.min_ask_volume_bitmex, 
                                     buy_real_volume=buy_real_volume, 
                                     buy_fee=self.bitmex_fee,
                                     sell_price=row.max_bid_price_deribit, 
                                     sell_real_price=sell_real_price,
                                     sell_volume=row.max_bid_volume_deribit,
                                     sell_real_volume=sell_real_volume,
                                     sell_fee=self.deribit_fee
                                    )
    
                    print('---'*10)
        
                elif (buy_deribit_coef > self.threshold) and (buy_deribit_coef > buy_bitmex_coef):
                    #buy on deribit, sell on bitmex
                    
                    i = self.both_df.index.searchsorted(self.actual_date)
                    if i >= self.both_df.shape[0]:
                        break
                    print('Deribit buy')
                    buy_real_price, buy_real_volume = self.both_df.iloc[i][['min_ask_price_deribit', 'min_ask_volume_deribit']].values
                    sell_real_price, sell_real_volume = self.both_df.iloc[i][['max_bid_price_bitmex', 'max_bid_volume_bitmex']].values
                    
                    self._make_order(
                         current_date=current_date,
                        coef=buy_deribit_coef,
                         buy_price=row.min_ask_price_deribit,
                         buy_real_price=buy_real_price, 
                         buy_volume=row.min_ask_volume_deribit, 
                         buy_real_volume=buy_real_volume, 
                         buy_fee=self.deribit_fee,
                         sell_price=row.max_bid_price_bitmex, 
                         sell_real_price=sell_real_price,
                         sell_volume=row.max_bid_volume_bitmex,
                         sell_real_volume=sell_real_volume,
                         sell_fee=self.bitmex_fee
                    )
                    
                    print('---'*10)
                    