from pxr import Sdf, Gf
import carb
import carb.events
import omni.usd

from omni.kit.scripting import BehaviorScript

from omni.iot.twinmaker.utils.omni_utils import get_data_binding_from_prim, get_data_bounds_attributes_from_prim
from omni.iot.twinmaker.store import DataBindingStore


class ModelScaler(BehaviorScript):
    def on_init(self):
        self.__init_attributes()
        self.__init_scale_attributes()

        self._is_playing = False
        self._last_data_timestamp = None

        carb.log_info(f"{__class__.__name__}.on_init()->{self.prim_path}")

    def on_destroy(self):
        if self._data_binding:
            DataBindingStore.get_instance().unsubscribe(self._data_binding)
        carb.log_info(f"{__class__.__name__}.on_destroy()->{self.prim_path}")

    def on_play(self):
        self._is_playing = True
        carb.log_info(f"{__class__.__name__}.on_play()->{self.prim_path}: subscribe {self._data_binding}")
        DataBindingStore.get_instance().subscribe(self._data_binding)
        context = omni.usd.get_context()
        context.set_pickable(str(self.prim_path), True)
        carb.log_info(f"{__class__.__name__}.on_play()->{self.prim_path}")

    def on_pause(self):
        self._running_time = 0
        carb.log_info(f"{__class__.__name__}.on_pause()->{self.prim_path}")

    def on_stop(self):
        self._running_time = 0
        self.reset_scale()
        DataBindingStore.get_instance().unsubscribe(self._data_binding)
        carb.log_info(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        if self._is_playing:
            latest_datapoint = DataBindingStore.get_instance().get_latest_datapoint(self._data_binding)
            if (not self._last_data_timestamp and latest_datapoint) or \
                (self._last_data_timestamp is not None and latest_datapoint.timestamp is not None \
                    and latest_datapoint.timestamp > self._last_data_timestamp):
                val = self._bounds.normalize(float(latest_datapoint.value))
                new_scale = Gf.Vec3f(self._default_scale[0], self._default_scale[1], val)
                carb.log_info(f"setting scale with [{latest_datapoint.value}@{latest_datapoint.timestamp}] => {new_scale}")
                self.update_scale(new_scale)

                self._last_data_timestamp = latest_datapoint.timestamp

    # Get attributes from prim with property data binding
    def __init_attributes(self):
        self._data_binding = get_data_binding_from_prim(self.prim)
        self._bounds = get_data_bounds_attributes_from_prim(self.prim, 0, 1)

    def __init_scale_attributes(self):
        scale = self.prim.GetAttribute('xformOp:scale').Get()
        self._default_scale = scale if scale is not None else Gf.Vec3f(1.0, 1.0, 1.0)
        carb.log_info(f'default scale {self._default_scale}')
    
    def update_scale(self, scale):
        self.prim.GetAttribute('xformOp:scale').Set(scale)
    
    def reset_scale(self):
        self.update_scale(self._default_scale)

    def is_prim_selected(self):
        return self.selection.is_prim_path_selected(self.prim_path.__str__())
    