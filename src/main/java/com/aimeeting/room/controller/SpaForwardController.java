package com.aimeeting.room.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/** Serves Vue history-mode routes from the packaged frontend. */
@Controller
public class SpaForwardController {

    @GetMapping({"/login", "/stock-watch", "/config"})
    public String forwardFrontendRoute() {
        return "forward:/index.html";
    }
}
