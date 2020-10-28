if ("ssd1306" in self.config["board"]["capabilities"] and self.config["board"]["capabilities"]["ssd1306"]):
            try:
                if (self.ssd1306 is None):
                    print("sensors: SSD1306 OLED initializing")
                    import ssd1306
                    self.ssd1306 = ssd1306.SSD1306_I2C(128, 64, self.i2cbus, int(self.config["board"]["i2c"]["ssd1306"]))
                    self.ssd1306.fill(0)
                    self.ssd1306.text(self.config["board"]["id"],0,0)
                    self.ssd1306.show()
                    print("sensors: SSD1306 OLED initialized")
            except BaseException as e:
                print("sensors:An exception occurred during mcp23017 activation")
                import sys
                sys.print_exception(e)