/***
 * Demo: LED Toggle
 *
 * PB5   ------> LED+
 * GND   ------> LED-
 */
#include "py32f0xx_bsp_printf.h"
#include "py32f0xx_hal.h"

static void APP_GPIO_Config(void);
static void APP_SystemClockConfig(void);
void APP_ErrorHandler(void);

int main(void) {
  HAL_Init();
  // APP_SystemClockConfig();

  APP_GPIO_Config();
  BSP_USART_Config();
  printf("PY32F0xx LED Toggle Demo\r\nSystem Clock: %ld\r\n", SystemCoreClock);

  while (1) {
    HAL_Delay(1000);
    HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_6);
    printf("preved\r\n");
  }
}

static void APP_SystemClockConfig(void) {
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType =
      RCC_OSCILLATORTYPE_HSE | RCC_OSCILLATORTYPE_HSI | RCC_OSCILLATORTYPE_LSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON; /* HSI ON */
  RCC_OscInitStruct.HSICalibrationValue =
      RCC_HSICALIBRATION_24MHz;             /* Set HSI clock 24MHz */
  RCC_OscInitStruct.HSIDiv = RCC_HSI_DIV1;  /* No division */
  RCC_OscInitStruct.HSEState = RCC_HSE_OFF; /* OFF */
  RCC_OscInitStruct.LSIState = RCC_LSI_OFF; /* OFF */

  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
    APP_ErrorHandler();
  }

  /* Reinitialize AHB,APB bus clock */
  RCC_ClkInitStruct.ClockType =
      RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_PCLK1;
  RCC_ClkInitStruct.SYSCLKSource =
      RCC_SYSCLKSOURCE_HSI; /* Select HSI as SYSCLK source */
  RCC_ClkInitStruct.AHBCLKDivider =
      RCC_SYSCLK_DIV1;                              /* APH clock, no division */
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1; /* APB clock, no division */

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) {
    APP_ErrorHandler();
  }
}

static void APP_GPIO_Config(void) {
  GPIO_InitTypeDef GPIO_InitStruct;

  __HAL_RCC_GPIOB_CLK_ENABLE();
  GPIO_InitStruct.Pin = GPIO_PIN_6;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
}

void APP_ErrorHandler(void) {
  printf("ERROR\n");
  while (1) {
  }
}

#ifdef USE_FULL_ASSERT
/**
 * @brief  Export assert error source and line number
 */
void assert_failed(uint8_t *file, uint32_t line) {
  /* printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  while (1)
    ;
}
#endif /* USE_FULL_ASSERT */
