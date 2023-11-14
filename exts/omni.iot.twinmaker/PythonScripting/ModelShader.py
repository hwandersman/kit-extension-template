import omni.usd
from datetime import datetime, timedelta
from omni.kit.scripting import BehaviorScript
import concurrent.futures
from pxr import Sdf, Gf

from .Main import get_state, get_executor
from .twinmaker_utils import date_to_iso
from .omni_utils import hexToVec3, getAllPrimChildren, bindMaterialCommand
from .TwinMaker import TwinMaker, DataBinding, RuleExpression
from .constants import WORKSPACE_ATTR, ASSUME_ROLE_ATTR, ENTITY_ATTR, COMPONENT_ATTR, PROPERTY_ATTR, REGION_ATTR, RULE_PROP_ATTR, RULE_OP_ATTR, RULE_VAL_ATTR, RULE_MAT_ATTR, BIND_ALL, RULE_COL_ATTR

class ModelShader(BehaviorScript):
    def on_init(self):
        self.__init_attributes()
        
        self._children = getAllPrimChildren(self.prim, [])

        self._runningTime = 0

        self._twinmaker = TwinMaker(self._region, self._assumeRoleARN, self._workspaceId)

        # Fetch property data type
        self._dataType = self._twinmaker.getPropertyValueType(self._dataBinding)
        self._dataType = '?'

        materialTargets = self.prim.GetRelationship('material:binding').GetTargets()
        if len(materialTargets) > 0:
            self._defaultMaterial = materialTargets[0]

        self._isRuleMatched = False
        self._changedMaterial = False

        print(f"{__class__.__name__}.on_init()->{self.prim_path}")

    # Get attributes from prim with property data binding
    def __init_attributes(self):
        # Get shared attributes from Logic object
        logicPrimPath = '/World/Logic'
        stage = omni.usd.get_context().get_stage()
        logicPrim = stage.GetPrimAtPath(logicPrimPath)
        self._workspaceId = logicPrim.GetAttribute(WORKSPACE_ATTR).Get()
        self._assumeRoleARN = logicPrim.GetAttribute(ASSUME_ROLE_ATTR).Get()
        self._region = logicPrim.GetAttribute(REGION_ATTR).Get()

        # Data binding attributes are on current prim
        entityId = self.prim.GetAttribute(ENTITY_ATTR).Get()
        componentName = self.prim.GetAttribute(COMPONENT_ATTR).Get()
        propertyName = self.prim.GetAttribute(PROPERTY_ATTR).Get()
        self._dataBinding = DataBinding(entityId, componentName, propertyName)

        # Rule for data binding attributes: prop op value (e.g. status == "ACTIVE")
        ruleProp = self.prim.GetAttribute(RULE_PROP_ATTR).Get()
        ruleOp = self.prim.GetAttribute(RULE_OP_ATTR).Get()
        ruleVal = self.prim.GetAttribute(RULE_VAL_ATTR).Get()
        self._ruleExpression = RuleExpression(ruleProp, ruleOp, ruleVal)
        
        # Material to change to when rule expression is true
        self._ruleMaterial = self.prim.GetAttribute(RULE_MAT_ATTR).Get()
        # Color to change to when rule expression is true
        self._ruleColor = self.prim.GetAttribute(RULE_COL_ATTR).Get()
        # Update all children prims when rule expression is true
        self._bindAllChildren = self.prim.GetAttribute(BIND_ALL).Get()
        
    def bind_material(self, materialPath, color):
        if self._bindAllChildren:
            for child in self._children:
                bindMaterialCommand(child.GetPath(), Sdf.Path(materialPath))
        else:
            bindMaterialCommand(self.prim_path, Sdf.Path(materialPath))
    
    # Rule material and color must be set as attributes on the object
    # Specify whether the rule is matched and the material should change
    def set_material(self, shouldChange):
        if shouldChange:
            self.bind_material(self._ruleMaterial, self._ruleColor)
        else:
            self.bind_material(self._defaultMaterial, self._defaultColor)

    def is_prim_selected(self):
        return self.selection.is_prim_path_selected(self.prim_path.__str__())

    # def on_destroy(self):
        # print(f"{__class__.__name__}.on_destroy()->{self.prim_path}")

    # def on_play(self):
        # print(f"{__class__.__name__}.on_play()->{self.prim_path}")

    def on_pause(self):
        self._runningTime = 0
        # print(f"{__class__.__name__}.on_pause()->{self.prim_path}")

    def on_stop(self):
        self._runningTime = 0
        # print(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        state = get_state()
        executor = get_executor()
        # Fetch data approx every 10 seconds
        frequency = 10
        
        # This script is sometimes initialized before Main.py
        if state is None:
            print('ModelShader state is not defined')
            return

        if state.is_play:
            # Math is finicky
            if round(self._runningTime % frequency, 2) - 0.035 < 0:
                endTime = datetime.now()
                startTime = endTime - timedelta(minutes=1)
                processes = []
                # Fetch alarm status in background process
                future = executor.submit(self._twinmaker.matchRule, self._dataBinding, self._dataType, date_to_iso(startTime), date_to_iso(endTime), self._ruleExpression)
                processes.append(future)
                for _ in concurrent.futures.as_completed(processes):
                    result = _.result()
                    self.set_material(result)
            self._runningTime = self._runningTime + delta_time
        else:
            self.set_material(False)
