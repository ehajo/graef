import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome.const import CONF_ID

tm1651_ns = cg.esphome_ns.namespace('tm1651')
TM1651Component = tm1651_ns.class_('TM1651Component', cg.Component)

CONF_PIN_CLK = 'pin_clk'
CONF_PIN_DIO = 'pin_dio'

CONFIG_SCHEMA = cv.Schema({
    cv.Required(CONF_ID): cv.declare_id(TM1651Component),
    cv.Required(CONF_PIN_CLK): pins.gpio_output_pin_schema,
    cv.Required(CONF_PIN_DIO): pins.gpio_output_pin_schema,
}).extend(cv.COMPONENT_SCHEMA)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_pin_clk(await cg.gpio_pin_expression(config[CONF_PIN_CLK])))
    cg.add(var.set_pin_dio(await cg.gpio_pin_expression(config[CONF_PIN_DIO])))