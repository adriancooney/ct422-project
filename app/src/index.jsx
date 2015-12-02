import React from "react";
import Router from "react-router";

// Base styling
import "./index.scss";

// Start the router
Router.run(routes, Router.HistoryLocation, function(Handler, state) {
    React.render(<Handler data={data} />, document.getElementById("app"));
});

