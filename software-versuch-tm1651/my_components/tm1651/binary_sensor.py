import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from esphome.const import CONF_ID, CONF_NAME

tm1651_ns = cg.esphome_ns.namespace('tm1651')
TM1651Sensor = tm1651_ns.class_('TM1651Sensor', binary_sensor.BinarySensor, cg.PollingComponent)
TM1651Component = tm1651_ns.class_('TM1651Component')

CONF_TM1651_ID = 'tm1651_id'
CONF_KEY_INDEX = 'key_index'

CONFIG_SCHEMA = binary_sensor.BINARY_SENSOR_SCHEMA.extend({
    cv.Required(CONF_ID): cv.declare_id(TM1651Sensor),
    cv.Required(CONF_TM1651_ID): cv.use_id(TM1651Component),
    cv.Required(CONF_KEY_INDEX): cv.int_range(min=0, max=7),
    cv.Optional(CONF_NAME): cv.string,
}).extend(cv.polling_component_schema('500ms'))  # Update-Intervall von 500ms

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID], 500)  # Übergibt 500ms an den Konstruktor
    await cg.register_component(var, config)
    await binary_sensor.register_binary_sensor(var, config)
    parent = await cg.get_variable(config[CONF_TM1651_ID])
    cg.add(var.set_parent(parent))
    cg.add(var.set_key_index(config[CONF_KEY_INDEX]))