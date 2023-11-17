from pxr import Sdf, Gf
import carb
import carb.events
import omni.usd

from omni.kit.scripting import BehaviorScript

from omni.iot.twinmaker.utils.omni_utils import get_data_binding_from_prim, get_rule_exp_list_from_prim, hex_to_vec_3
from omni.iot.twinmaker.utils.twinmaker_utils import evaluate_rule
from omni.iot.twinmaker.store import DataBindingStore
from omni.iot.twinmaker.constants import MAT_COLOR_ATTR, CHANGE_MAT_PATH

class ModelShader(BehaviorScript):
    def on_init(self):
        self.__init_attributes()
        self.__init_material_attributes()

        self._is_playing = False
        self._last_data_timestamp = None
        
        self._is_rule_matched = False
        self._changed_material = False

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
        self.reset_material()
        DataBindingStore.get_instance().unsubscribe(self._data_binding)
        carb.log_info(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        #carb.log_info("update")
        if self._is_playing:
            latest_datapoint = DataBindingStore.get_instance().get_latest_datapoint(self._data_binding)
            #if latest_datapoint:
            #    carb.log_info(f"[{self._last_data_timestamp}, {latest_datapoint.timestamp}] {latest_datapoint.value}")
            if (not self._last_data_timestamp and latest_datapoint) or \
                (self._last_data_timestamp is not None and latest_datapoint.timestamp is not None \
                    and latest_datapoint.timestamp > self._last_data_timestamp):
                matched_rule_idx = evaluate_rule(self._rule_expression_list, latest_datapoint.value)
                carb.log_info(f"evaluating rule with [{latest_datapoint.value}@{latest_datapoint.timestamp}] => {matched_rule_idx}")

                if matched_rule_idx != -1:
                    self.change_material_from_idx(matched_rule_idx)

                self._last_data_timestamp = latest_datapoint.timestamp

    # Get attributes from prim with property data binding
    def __init_attributes(self):
        self._data_binding = get_data_binding_from_prim(self.prim)
        self._rule_expression_list = get_rule_exp_list_from_prim(self.prim)
        
        # Material to change to when rule expression is true
        # Store to keep track of the original color based on whether a rule will update it
        self._mat_color_list = self.prim.GetAttribute(MAT_COLOR_ATTR).Get()
        self._may_change_color = False
        for color in self._mat_color_list:
            if color != 'NONE':
                self._may_change_color = True

        self._mat_path_list = self.prim.GetAttribute(CHANGE_MAT_PATH).Get()

    def __init_material_attributes(self):
        stage = omni.usd.get_context().get_stage()
        # Get material
        material_targets = self.prim.GetRelationship('material:binding').GetTargets()
        if len(material_targets) > 0:
            prim_material_path = material_targets[0]
            shader_path = f'{prim_material_path}/Shader'
            self._shader_prim = stage.GetPrimAtPath(shader_path)

            # Only fetch attribute if it could be changed by matching a rule
            self._default_tint_color = None
            self._default_albedo_add = None
            if self._may_change_color:
                self._default_tint_color = self._shader_prim.GetAttribute('inputs:diffuse_tint').Get()
                # If the attribute is still the default it will show up as 'None'
                if self._default_tint_color is None:
                    self._default_tint_color = Gf.Vec3f(1.0, 1.0, 1.0)
                self._default_albedo_add = self._shader_prim.GetAttribute('inputs:albedo_add').Get()
                if self._default_albedo_add is None:
                    self._default_albedo_add = 0
            
            self._default_material = prim_material_path
        else:
            raise Exception('ModelShader attached to prim without a material binding')
    
    def may_update_var(self, var_list):
        for var in var_list:
            if var != 'NONE':
                return True
        return False
    
    def update_shader(self, tint_color, albedo_add, material_path):
        if tint_color is not None:
            self._shader_prim.GetAttribute('inputs:diffuse_tint').Set(tint_color)
            self._shader_prim.GetAttribute('inputs:albedo_add').Set(albedo_add)
        elif material_path != 'NONE':
            omni.kit.commands.execute(
                'BindMaterialCommand',
                prim_path=self.prim_path,
                material_path=Sdf.Path(material_path),
                strength=['strongerThanDescendants']
            )
    
    # Rule color must be set as attribute lists on the object
    # Specify the index of the matched rule
    def change_material_from_idx(self, i):
        mat_color = self._mat_color_list[i]
        mat_color = None if mat_color == 'NONE' else hex_to_vec_3(mat_color)
        mat_path = self._mat_path_list[i]
        mat_path = None if mat_path == 'NONE' else mat_path

        if mat_color is None and mat_path is None:
            self.reset_material() 
        else:
            self.update_shader(mat_color, 0.5, mat_path)
    
    def reset_material(self):
        self.update_shader(self._default_tint_color, self._default_albedo_add, self._default_material)

    def is_prim_selected(self):
        return self.selection.is_prim_path_selected(self.prim_path.__str__())
    