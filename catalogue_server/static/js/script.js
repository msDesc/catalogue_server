// LEGACY CODE -- For Reference Only

$(function ()
{
    $(document).on("submit", ".search-query-form", function (e)
    {
        var q = $(".search-query-form").find("#q").val();

        if (q.length === 0)//check to see if the search field is empty;
        {
            //if it is, show all records 
            e.preventDefault();
            window.location.href = "/?utf8=✓&search_field=default";
        }
    });

    if ($(".individual-item").is(":visible"))
    {
        var page = "";

        $(".browse-item").each(function (key, val)
        {   //loop through the browse items
            page = $(val).data("page");//get the data value from the browse items

            if (window.location.href.indexOf(page) > -1)
            {//check if the data value from the browse items is the same as the current page
                $(".browse-item[data-page=" + page + "]").addClass("browse-item-active");//make the browse item active based on the current page
            }
        });

        var name = encodeURI($("h1[itemprop^=name]").text()).replace(/'/g, "%27");

        $.ajax({
            //            url: "https://api.zotero.org/groups/434020/items?tag=" + name + "&format=keys",
            url: "https://api.zotero.org/users/3118282/items?tag=" + name + "&format=keys",
            type: "GET"
        }).done(function (data)
        {
            var lines = [];
            $.each(data.split(/\n/), function (i, line)
            {
                if (line !== "")
                {
                    lines.push(line);
                }
            });

            //Only show the bibliography if there are results.
            if (lines.length > 0)
            {
                var bibliography = $("<div class='zotero-bibliography'></div>");
                var fieldTitle = "<h3>Zotero bibliography</h3>";
                bibliography.append(fieldTitle);

                // if records have been found, then show how many are available and display a to Zotero website
                var link = "https://www.zotero.org/bodleianwmss/items/tag/";
                var fieldValue = "<div id='zotero-bibliography-text'>" + lines.length + " item(s) related to this MS. have been found in our <a target='_blank' href='" + link + name + "'>bibliographical database.</a></div>";
                bibliography.append(fieldValue);
                $(".tei-body").append(bibliography);
            }
        }).fail(function (data)
        {
            console.log(data);
        });
    }
});

//event which checks when the contact form is submitted
$("#contact-us-form").submit(function (e)
{
    //check if the magic field is empty
    if ($("#contact-miere").val() != "")
    {
        //if it is, do nothing
        console.log("no no");
        $("#submit-email").html("Invalid form").addClass("fail-captcha").attr("disabled", "disabled").delay(2500).fadeIn("slow", function ()
        {
            $("#submit-email").html("Send").removeClass("fail-captcha").removeAttr("disabled");
        });
        e.preventDefault();
        return false;
    }
});

//event triggered when the the contact us form is successfully submitted
$(document).ajaxComplete(function (event, request, settings)
{
    var text = $(".modal-content").text();

    //check the message that's coming from the back-end validation
    if (~text.indexOf("Robot"))
    {
        //if there was an issue, display an appropriate message that disappears after 2.5 seconds
        $("#submit-email").html("Invalid form").addClass("fail-captcha").attr("disabled", "disabled").delay(2500).fadeIn("slow", function ()
        {
            $("#submit-email").html("Send").removeClass("fail-captcha").removeAttr("disabled");
        });
    }
    else
    {
        // if everything went well, display a success message
        $("body").removeClass("modal-open");
        $("#submit-email").html("Thank you!").removeClass("fail-captcha").addClass("success-captcha").delay(2500).fadeIn("slow", function ()
        {
            $("#submit-email").html("Send").removeClass("success-captcha").removeAttr("disabled");
            $('#contact-us-form').trigger("reset");
        });
    }
});

//event which starts when the contact form is submitted
$(document).ajaxStart(function (e)
{
    $("#submit-email").html("Pending...").attr("disabled", "disabled");
});


$(document).on("click", ".more_facets_link", function (e)
{
    e.stopPropagation();
    $("#ajax-modal, .modal-dialog, .modal-content").removeClass("contact-nfo");
    setTimeout(function ()
    {
        $(".modal-backdrop").show().css({
            "z-index": "1040",
            "left": "0",
            "top": "0",
            "width": "100%",
            "height": "100%"
        });
    }, 500);
});

$(document).on("click", ".advanced-search-form .panel-title", function ()
{
    $("span.facet-count").removeAttr("style");
});