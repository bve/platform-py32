
#include "main.h"
#include "py32f0xx_bsp_printf.h"


static void APP_SystemClockConfig(void);
static void APP_GPIOConfig(void);


int main(void) {
  APP_SystemClockConfig();
  APP_GPIOConfig();

  BSP_USART_Config(115200);
  printf("PY32F0xx GPIO Example\r\nClock: %ld\r\n", SystemCoreClock);

  while (1)  {
    LL_GPIO_TogglePin(GPIOA, LL_GPIO_PIN_0);
    printf("Hello!\r\n");
    LL_mDelay(1000);
  }
}

static void APP_SystemClockConfig(void) {
  LL_RCC_HSI_Enable();
  while(LL_RCC_HSI_IsReady() != 1);

  LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
  LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_HSISYS);
  while(LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_HSISYS);

  LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_1);
  // TODO this is wrong as HSI is 24mhz... probably designed for different MCU??
  LL_Init1msTick(8000000);
  LL_SetSystemCoreClock(8000000);
}


static void APP_GPIOConfig(void) {
  // PA0
  LL_IOP_GRP1_EnableClock(LL_IOP_GRP1_PERIPH_GPIOA);
  LL_GPIO_SetPinMode(GPIOA, LL_GPIO_PIN_0, LL_GPIO_MODE_OUTPUT);
}

void APP_ErrorHandler(void) {
  while (1);
}

#ifdef  USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  while (1);
}
#endif /* USE_FULL_ASSERT */
