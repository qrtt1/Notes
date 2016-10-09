package hello;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class GreetingController {

    @Autowired ConcreteClass aSet;

    @Autowired ConcreteClass bSet;

    @RequestMapping("/aSet")
    public ConcreteClass aSet() {
        return aSet;
    }

    @RequestMapping("/bSet")
    public ConcreteClass bSet() {
        return bSet;
    }
}