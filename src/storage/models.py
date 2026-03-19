from peewee import Model, CharField, FloatField, IntegerField, DateTimeField, BooleanField, DateField
from storage.db import db
from utils.time_utils import utc_now

class BaseModel(Model):
    class Meta:
        database = db

class Prices(BaseModel):
    symbol = CharField(max_length=50)
    name = CharField(max_length=150)
    price = FloatField()
    change_pct = FloatField()
    volume = IntegerField(null=True)
    timestamp = DateTimeField(default=utc_now)
    source = CharField(max_length=50)
    is_delayed = BooleanField(default=False)
    currency = CharField(max_length=10, default="INR")
    
    class Meta:
        indexes = (
            (('symbol', 'timestamp'), False),
        )

class DailyEOD(BaseModel):
    symbol = CharField(max_length=50)
    open = FloatField(null=True)
    high = FloatField(null=True)
    low = FloatField(null=True)
    close = FloatField()
    volume = IntegerField(null=True)
    oi = IntegerField(null=True)
    date = DateField()
    source = CharField(max_length=50)

    class Meta:
        indexes = (
            (('symbol', 'date'), False),
        )

class FO_OI(BaseModel):
    symbol = CharField(max_length=50)
    expiry = DateField()
    strike = FloatField()
    option_type = CharField(max_length=2) # CE or PE
    oi = IntegerField()
    oi_change = IntegerField()
    timestamp = DateTimeField(default=utc_now)

    class Meta:
        indexes = (
            (('symbol', 'timestamp'), False),
        )

class OptionsSnapshot(BaseModel):
    symbol = CharField(max_length=50)
    expiry = DateField()
    pcr = FloatField()
    max_pain = FloatField()
    iv_rank = FloatField()
    atm_iv = FloatField()
    timestamp = DateTimeField(default=utc_now)

    class Meta:
        indexes = (
            (('symbol', 'timestamp'), False),
        )

class Events(BaseModel):
    symbol = CharField(max_length=50, null=True)
    event_type = CharField(max_length=100)
    headline = CharField(max_length=500)
    source = CharField(max_length=50)
    timestamp = DateTimeField(default=utc_now)
    keywords_matched = CharField(max_length=200, null=True)

    class Meta:
        indexes = (
            (('symbol', 'timestamp'), False),
        )

class TradeFlows(BaseModel):
    commodity = CharField(max_length=100)
    reporter_country = CharField(max_length=100)
    partner_country = CharField(max_length=100)
    trade_type = CharField(max_length=20) # import or export
    value_usd = FloatField(null=True)
    quantity = FloatField(null=True)
    unit = CharField(max_length=50, null=True)
    year = IntegerField()
    source = CharField(max_length=50)

class MacroSeries(BaseModel):
    indicator_code = CharField(max_length=100)
    indicator_name = CharField(max_length=200)
    country = CharField(max_length=100)
    value = FloatField()
    period = CharField(max_length=50, null=True)
    timestamp = DateTimeField(default=utc_now)
    source = CharField(max_length=50)

    class Meta:
        indexes = (
            (('indicator_code', 'timestamp'), False),
        )

class HedgingFlags(BaseModel):
    filing_type = CharField(max_length=50) # e.g. 13F-HR
    filer_name = CharField(max_length=200)
    asset_type = CharField(max_length=100)
    position_type = CharField(max_length=50)
    current_qty = FloatField(null=True)
    prev_qty = FloatField(null=True)
    change_pct = FloatField(null=True)
    signal = CharField(max_length=50) # increase/decrease/unwinding
    filing_date = DateField()
    source = CharField(max_length=50)

    class Meta:
        indexes = (
            (('filer_name', 'filing_date'), False),
        )

class SupplyEvents(BaseModel):
    commodity = CharField(max_length=100)
    event_type = CharField(max_length=100)
    value = FloatField(null=True)
    unit = CharField(max_length=50, null=True)
    signal = CharField(max_length=50) # bullish/bearish/neutral
    timestamp = DateTimeField(default=utc_now)
    source = CharField(max_length=50)

    class Meta:
        indexes = (
            (('commodity', 'timestamp'), False),
        )

class SanctionsWatch(BaseModel):
    entity_name = CharField(max_length=300)
    country = CharField(max_length=100, null=True)
    asset_type = CharField(max_length=100, null=True)
    list_type = CharField(max_length=100)
    added_date = DateField(null=True)
    source = CharField(max_length=50)
