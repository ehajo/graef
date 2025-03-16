import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import output
from esphome.const import CONF_ID

tm1651_ns = cg.esphome_ns.namespace('tm1651')
TM1651Output = tm1651_ns.class_('TM1651Output', output.BinaryOutput)
TM1651Component = tm1651_ns.class_('TM1651Component')

CONF_TM1651_ID = 'tm1651_id'
CONF_SEGMENT = 'segment'

CONFIG_SCHEMA = output.BINARY_OUTPUT_SCHEMA.extend({
    cv.Required(CONF_ID): cv.declare_id(TM1651Output),
    cv.Required(CONF_TM1651_ID): cv.use_id(TM1651Component),
    cv.Required(CONF_SEGMENT): cv.int_range(min=0, max=7),
})

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await output.register_output(var, config)
    parent = await cg.get_variable(config[CONF_TM1651_ID])
    cg.add(var.set_parent(parent))
    cg.add(var.set_segment(config[CONF_SEGMENT]))