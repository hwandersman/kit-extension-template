from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Timer
from datetime import datetime, timedelta
import asyncio
import carb

import omni.kit.app

from omni.iot.twinmaker.twinmaker_api import TwinMaker
from omni.iot.twinmaker.data_models import DataBinding
from omni.iot.twinmaker.utils.omni_utils import get_global_config
from omni.iot.twinmaker.utils.twinmaker_utils import date_to_iso

class DataFetchingWorker:
    """
    Fetch data on a given interval. Relies on threading.Timer, which runs a function once after a
    certain number of seconds. This creates a Timer object on a regular interval to execute a given function repeatedly.
    """
    def __init__(self, interval, region, role, workspace_id):
        self.interval = interval

        self._executor = ThreadPoolExecutor(max_workers=4)
        self._twinmaker = TwinMaker(region, role, workspace_id)
        self._subscription_handle = None

        self._is_fetching = False
        self._last_fetch_endtime = datetime.now() - timedelta(seconds=15)
        self._data_fetching_tasks = set()

        self._subscribed_databindings = set()
        self._databinding_valuetype = dict()
        self._in_mem_store = dict()

    def _on_update(self, e):
        # carb.log_info(f'on_update event: {e.payload}')
        # check if there is an ongoing data fetching
        if self._is_fetching:
            return
        
        # carb.log_info(f'last fetch time {self._last_fetch_endtime}')

        # check if at least interval second has passed after last fetch
        if self._last_fetch_endtime + timedelta(seconds=self.interval) > datetime.now():
            return
        
        # carb.log_info(f'we should fetch!')
        
        # fetch data
        self._is_fetching = True
        self._schedule_data_fetching()

    def _schedule_data_fetching(self):
        carb.log_info('schedule data fetching tasks')
        try:
            asyncio.ensure_future(self._async_fetch_data())
        except RuntimeError as e:
            carb.log_error(f'failed to complete data fetching tasks, error: {e}')

    async def _async_fetch_data(self):
        loop = asyncio.get_event_loop()
        fetch_end_time = datetime.now()
        blocking_tasks = []
        carb.log_info('start fetching data types')
        carb.log_info(f'total subs {len(self._subscribed_databindings)}')
        for d in self._subscribed_databindings:
            if d not in self._databinding_valuetype:
                blocking_tasks.append(loop.run_in_executor(self._executor, self._get_property_value_type, d))
        
        if len(blocking_tasks) > 0:
            await asyncio.wait(blocking_tasks)

        carb.log_info('fetching data types completed')

        carb.log_info('start data fetching job')
        carb.log_info(f'total subs {len(self._subscribed_databindings)}')
        blocking_tasks = []
        for d in self._subscribed_databindings:
            blocking_tasks.append(loop.run_in_executor(self._executor, self._get_latest_property_value, 
                                                       d, self._databinding_valuetype[d], 
                                                       date_to_iso(self._last_fetch_endtime), date_to_iso(fetch_end_time)))
        
        if len(blocking_tasks) > 0:
            await asyncio.wait(blocking_tasks)

        carb.log_info('fetching data job completed')
        self._is_fetching = False
        self._last_fetch_endtime = fetch_end_time
    
    def _get_property_value_type(self, databinding):
        carb.log_info(f'fetching data type for property {databinding}')
        property_value_type = self._twinmaker.get_property_value_type(databinding)
        self._databinding_valuetype[databinding] = property_value_type
        carb.log_info(f'got data type for property {databinding}: {property_value_type}')

    def _get_latest_property_value(self, databinding, datatype, starttime, endtime):
        carb.log_info(f'fetching latest value for property {databinding}')
        result = self._twinmaker.get_latest_property_value(databinding, datatype, starttime, endtime)
        carb.log_info(f'got latest value for property {databinding}: {result}')
        self._in_mem_store[databinding] = result

    def start(self):
        if not self._subscription_handle:
            self._subscription_handle = omni.kit.app.get_app() \
                .get_update_event_stream().create_subscription_to_pop(self._on_update, name="UPDATE_SUB")

    def stop(self):
        self._subscription_handle = None
        self._is_fetching = False


class DataBindingStore:

    __instance: DataBindingStore = None
    
    @classmethod
    def get_instance(cls) -> DataBindingStore:
        if cls.__instance is None:
            cls.__instance = DataBindingStore()
        return cls.__instance

    def __init__(self):
        global_config = get_global_config()
        self._worker = DataFetchingWorker(2, 
                                          global_config['region'],
                                          global_config['role'], 
                                          global_config['workspace_id'])
        
    
    # force create a new 'singleton' to workaround the sync issue between Scripting and extension
    @classmethod
    def force_reinit(cls) -> DataBindingStore:
        cls.__instance = None
        return cls.get_instance()

    def start_data_fetching(self):
        self._worker.start()

    def stop_data_fetching(self):
        self._worker.stop()

    def subscribe(self, databinding: DataBinding):
        carb.log_info(f'adding {databinding} to subscription')
        self._worker._subscribed_databindings.add(databinding)
        carb.log_info(f'total subs {len(self._worker._subscribed_databindings)}')

    def unsubscribe(self, databinding: DataBinding):
        carb.log_info(f'removing {databinding} from subscription')
        if databinding in self._worker._subscribed_databindings:
            self._worker._subscribed_databindings.remove(databinding)
        carb.log_info(f'total subs {len(self._worker._subscribed_databindings)}')
        # TODO: clear in mem states
        
    def get_latest_datapoint(self, databinding: DataBinding):
        if databinding in self._worker._in_mem_store:
            return self._worker._in_mem_store[databinding]
        else:
            return None