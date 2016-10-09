package hello;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

@Configuration
@ComponentScan
public class AppConfig {

    static Log logger = LogFactory.getLog(AppConfig.class);

    @ConfigurationProperties(prefix = "aSet")
    @Bean
    ConcreteClass aSet() {
        return new ConcreteClass();
    }

    @ConfigurationProperties(prefix = "bSet")
    @Bean
    ConcreteClass bSet() {
        return new ConcreteClass();
    }

}
