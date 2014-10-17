/**
 * Created by jeff on 10/14/14.
 */
function graphVals(graph_data, units, varName) {


            var minDate = new Date(graph_data[0].x);
            var maxDate = new Date(graph_data[graph_data.length - 1].x);

            var WIDTH = 800,
                HEIGHT = 432,
                HEIGHT2 = 50,
                MARGINS = {
                  top: 20,
                  right: 40,
                  bottom: 20,
                  left: 80
                },

                xRange = d3.time.scale().range([MARGINS.left,WIDTH]).domain([minDate, maxDate ]),
                xRange2 = d3.time.scale().range([MARGINS.left, WIDTH]).domain([minDate, maxDate ]),
                yRange = d3.scale.linear().range([HEIGHT - MARGINS.top, MARGINS.bottom]).domain([d3.min(graph_data, function(d) {
                  return d.y;
                }), d3.max(graph_data, function(d) {
                  return d.y;
                })]),
                yRange2 = d3.scale.linear().range([HEIGHT2 - MARGINS.top, MARGINS.bottom]).domain([d3.min(graph_data, function(d) {
                  return d.y;
                }), d3.max(graph_data, function(d) {
                  return d.y;
                })]),
                xAxis = d3.svg.axis()
                  .scale(xRange)
                  .tickSize(5)
                  .tickSubdivide(true),
                yAxis = d3.svg.axis()
                  .scale(yRange)
                  .tickSize(5)
                  .orient('left')
                  .tickSubdivide(true);

            $("#graph-container").html("");

            var svg = d3.select("#graph-container").append("svg")
                .attr("width", 833)
                .attr("height", 500);

    var over = svg.append("g")
                .attr("class", "over")
                .style("display", "none");

            over.append("circle")
                .attr("r", 4.5);

            over.append("text")
                .attr("x", 9)
                .attr("dy", ".35em");

            svg.append("clipPath")
                .attr("id", "clip")
                .append("rect")
                .attr("width",  WIDTH-MARGINS.right-40)
                .attr("x",MARGINS.left)
                .attr("height", HEIGHT);


            svg.append("rect")
                .attr("class", "overlay")
                .attr("width",  WIDTH-MARGINS.right-40)
                .attr("x",MARGINS.left)
                .attr("height", HEIGHT)
                .on("mouseover", function() { over.style("display", null); })
                .on("mouseout", function() { over.style("display", "none"); })
                .on("mousemove", mousemove);

            var brush = d3.svg.brush()
                .x(xRange2)
                .on("brush", brushed);

            var focus = svg.append("g")
                .attr("class", "focus")
                .attr("width", 762)
                .attr("height", 300);

            focus.append('g')  // Add the x axis
                .attr('class', 'x axis')
                .attr('transform', 'translate(0,' + (HEIGHT - MARGINS.bottom) + ')')
                .call(xAxis);

            focus.append('g')  // Add the y axis
                .attr('class', 'y axis')
                .attr('transform', 'translate(' + (MARGINS.left) + ',0)') // not totally sure this is necessary
                .call(yAxis);

            svg.append("text")  // y axis label
                .attr("transform", "rotate(-90)")
                .attr("y", 6)
                .attr("x",0 - (HEIGHT / 2))
                .attr("dy", ".75em")
                .attr("text-anchor", "middle")
                .text(varName + " ("+units+")");


            var lineFunc = d3.svg.line()
              .x(function(d) {
                return xRange(d.x);
              })
              .y(function(d) {
                return yRange(d.y);
              })
              .interpolate('linear');

            var lineFunc1 = d3.svg.line()
              .x(function(d) {
                return xRange(d.x);
              })
              .y(function(d) {
                return yRange2(d.y);
              })
              .interpolate('linear');

            focus.append('path')
                .attr('d', lineFunc(graph_data))
                .attr('stroke', 'rgb(31,119,180)')
                .attr('class','line')
                .attr('stroke-width', 1.5)
                .attr("clip-path", "url(#clip)")
                .attr('fill', 'none');

            var bisectDate = d3.bisector(function(d) { return d.x; }).left;

             function mousemove() {
                 var x0 = xRange.invert(d3.mouse(this)[0]),
                 i = bisectDate(graph_data, x0, 1),
                 d0 = graph_data[i - 1],
                 d1 = graph_data[i],
                 d = x0 - d0.x > d1.x - x0 ? d1 : d0;
                 console.log(x0);
            over.attr("transform", "translate(" + xRange(d.x) + "," + yRange(d.y) + ")");
            over.select("text").text(d.y);
            over.select("text").attr("transform","translate(0,8)");
             }


            var context = svg.append("g")
                .attr("class", "context")
                .attr("transform", "translate(0," + HEIGHT + ")");



            context.append('g')
              .attr('class', 'x axis')
              .attr('transform', 'translate(0,' + (HEIGHT2 - MARGINS.bottom) + ')')
              .call(xAxis);


            context.append('path')
              .attr('d', lineFunc1(graph_data))
              .attr('stroke', 'rgb(31,119,180)')
              .attr('stroke-width', 1.5)
              .attr('class','line')
              .attr('fill', 'none');

            context.append("g")
              .attr("class", "x brush")
              .call(brush)
            .selectAll("rect")
              .attr("y", 0)
              .attr("height", 35);
        function brushed() {
          xRange.domain(brush.empty() ? xRange2.domain() : brush.extent());
          var x0 = brush.extent()[0],
              x1 = brush.extent()[1],
              xpos0 = bisectDate(graph_data,x0,1),
              xpos1 = bisectDate(graph_data,x1,1),
              subData = graph_data.slice(xpos0,xpos1),
              subMin = d3.min(subData, function(d) {
                  return d.y;
                }),
              subMax = d3.max(subData, function(d) {
                  return d.y;
                });
          yRange.domain(brush.empty() ? yRange2.domain() : [subMin,subMax]);
          focus.select(".line").attr("d", lineFunc(graph_data));
          focus.select(".x.axis").call(xAxis);
          focus.select(".y.axis").call(yAxis);
          var summary = calcSummaryStats(subData);
          if (brush.empty()){summary = calcSummaryStats(graph_data)}
          setSummaryStatistics(summary);
            }
        var summary = calcSummaryStats(graph_data);
        setSummaryStatistics(summary);
        getDatasetsAfterFilters(glob_graph_data);
        }

function calcSummaryStats(data){
            var summary = {};
            summary = {
                maximum:-Infinity,
                minimum:Infinity,
                arithmeticMean: 0,
                geometricSum:0,
                geometricMean:0,
                deviationSum:0,
                standardDeviation:0,
                observations:0,
                coefficientOfVariation:0,
                quantile10:0,
                quantile25:0,
                median:0,
                quantile75:0,
                quantile90:0
            };

            if (data.length == 0){
                summary.maximum = "NaN";
                summary.minimum = "NaN";
                summary.arithmeticMean = "NaN";
                summary.geometricSum = "NaN";
                summary.geometricMean = "NaN";
                summary.deviationSum = "NaN";
                summary.standardDeviation = "NaN";
                summary.observations = 0;
                summary.quantile10 = "NaN";
                summary.quantile25 = "NaN";
                summary.median = "NaN";
                summary.quantile75 = "NaN";
                summary.quantile90 = "NaN";
            }
           else {
                var y_vals = [];
                for (var j = 0; j < data.length; j++) {
                    y_vals.push(data[j].y)
                }
                // Quantiles
                summary.quantile10 = d3.quantile(y_vals, .1).toFixed(2);
                summary.quantile25 = d3.quantile(y_vals, .25).toFixed(2);
                summary.median = d3.quantile(y_vals, .5).toFixed(2);
                summary.quantile75 = d3.quantile(y_vals, .75).toFixed(2);
                summary.quantile90 = d3.quantile(y_vals, .9).toFixed(2);
                // Number of observations
                summary.observations = data.length;
                // Maximum and Minimum
                summary.maximum = d3.max(data, function (d) {
                    return d.y;
                });  //good
                summary.minimum = d3.min(data, function (d) {
                    return d.y;
                });  //good

                // Arithmetic Mean
                summary.arithmeticMean = d3.mean(data, function (d) {
                    return d.y;
                }).toFixed(2);

                // Standard Deviation
                summary.deviationSum = d3.sum(data, function (d) {
                    return Math.pow(parseFloat(d.y) - summary.arithmeticMean, 2)
                }).toFixed(2);
                summary.standardDeviation = (Math.pow(summary.deviationSum / data.length, (1 / 2))).toFixed(2);

                // Geometric Mean
                summary.geometricSum = d3.sum(data, function (d) {
                    if (d.y != 0) return Math.log(Math.abs(d.y));
                }).toFixed(2);
                summary.geometricMean = (Math.pow(2, (summary.geometricSum / data.length))).toFixed(2);

                // Coefficient of Variation
                var variation = summary.standardDeviation / summary.arithmeticMean;
                if (variation == Infinity || variation == -Infinity) {
                    variation = null;
                }
                summary.coefficientOfVariation = ((summary.standardDeviation / summary.arithmeticMean) * 100).toFixed(2) + "%";

                // Add commas
                summary.arithmeticMean = numberWithCommas(summary.arithmeticMean);
                summary.geometricMean = numberWithCommas(summary.geometricMean);
                summary.observations = numberWithCommas(summary.observations);
                summary.quantile10 = numberWithCommas(summary.quantile10);
                summary.quantile25 = numberWithCommas(summary.quantile25);
                summary.median = numberWithCommas(summary.median);
                summary.quantile75 = numberWithCommas(summary.quantile75);
                summary.quantile90 = numberWithCommas(summary.quantile90);
                return summary;
            }
    }

function numberWithCommas(x) {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            }


function setSummaryStatistics(summary){
        $("#statisticsTable tbody").empty();
        $("#statisticsTable tbody").append(
            '<tr><td>Arithmetic Mean</td><td>' + summary.arithmeticMean + '</td></tr>\
                    <tr><td>Geometric Mean</td><td>'+ summary.geometricMean + '</td></tr>\
                    <tr><td>Maximum</td><td>' + summary.maximum + '</td></tr>\
                    <tr><td>Minimum</td><td>' + summary.minimum + '</td></tr>\
                    <tr><td>Standard Deviation</td><td>' + summary.standardDeviation + '</td></tr>\
                    <tr><td>10%</td><td>'+ summary.quantile10 +'</td></tr>\
                    <tr><td>25%</td><td>'+ summary.quantile25 +'</td></tr>\
                    <tr><td>Median, 50%</td><td>'+ summary.median +'</td></tr>\
                    <tr><td>75%</td><td>'+ summary.quantile75 +'</td></tr>\
                    <tr><td>90%</td><td>'+ summary.quantile90 +'</td></tr>\
                    <tr><td>Number of Observations</td><td>'+ summary.observations +'</td></tr>'
        );
    }


function getDatasetsAfterFilters(dataset){
            var minDate = new Date(dataset[0].x);
            var maxDate = new Date(dataset[dataset.length - 1].x);

            // Update minimum and maximum dates on the date pickers
             var dateFirst = $('#dpd1').datepicker({
                onRender: function (date){
                    return (date.valueOf() > maxDate.valueOf() || date.valueOf() < minDate.valueOf()) ? 'disabled' : '';    // disable dates with no records
                }
            }).on('click', function(){
                dateLast.hide();
            }).on('changeDate',function (ev) {
                dateFirst.hide();
            }).data('datepicker');

            var dateLast = $('#dpd2').datepicker({
                onRender: function (date) {
                    return (date.valueOf() > maxDate.valueOf() || date.valueOf() < minDate.valueOf()) ? 'disabled' : '';    // disable dates with no records
                }
            }).on('click', function(){
                dateFirst.hide();
            }).on('changeDate',function (ev) {
                dateLast.hide();
            }).data('datepicker');

            var nowTemp = new Date();
            var now = new Date(nowTemp.getFullYear(), nowTemp.getMonth(), nowTemp.getDate(), 0, 0, 0, 0);

            // If no dates are set, display the last month. Display the whole set if it contains less than 500 data points.
            if (dateFirst.date.valueOf() == now.valueOf() && dateLast.date.valueOf() == now.valueOf()) {
                // Mark the button of last month interval
                $("#dateIntervals button").removeClass("active");
                $("#btnLastMonth").addClass("active");

                dateFirst.date = maxDate.setMonth(maxDate.getMonth() - 1);
                dateFirst.setValue(maxDate);

                dateLast.date = maxDate.setMonth(maxDate.getMonth() + 1);
                dateLast.setValue(maxDate);
            }

            // Update click events for the date interval buttons
            $("#btnLastWeek").click(function() {
                $("#dateIntervals button").removeClass("active");
                $(this).addClass("active");

                dateFirst.date = maxDate.setDate(maxDate.getDate() - 7);
                dateFirst.setValue(maxDate);

                dateLast.date = maxDate.setDate(maxDate.getDate() + 7);
                dateLast.setValue(maxDate);
            });
            $("#btnLastMonth").click(function() {
                $("#dateIntervals button").removeClass("active");
                $(this).addClass("active");

                dateFirst.date = maxDate.setMonth(maxDate.getMonth() - 1);
                dateFirst.setValue(maxDate);

                dateLast.date = maxDate.setMonth(maxDate.getMonth() + 1);
                dateLast.setValue(maxDate);
            });
            $("#btnAll").click(function() {
                $("#dateIntervals button").removeClass("active");
                $(this).addClass("active");

                dateFirst.date = minDate;
                dateFirst.setValue(minDate);

                dateLast.date = maxDate;
                dateLast.setValue(maxDate);
            });


            return dataset;
        }