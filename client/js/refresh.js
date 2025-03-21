
// data is a list
// We need to each element as a div
// in each div, we display the the first subelement as h1
// and the "similarity" in the second subelement as p
// display the image in "image_path" with a href to "web_url"

function refreshResults(resultData) {
    var result = '';
    var data = resultData['result'];
    var selected = resultData['selected'];
    console.log(data);
    for (var i = 0; i < data.length; i++) {
        const d = data[i];
        result += `
        <div class="case">
            <div class="case-head">
                <p class="case-title">${d.name}</p>
                <span class="info">Score: ${d.similarity}</span>
                ${selected[i] == 1 
                    ? `<span class="remove" data-caseid="${d.case_id}">&#x2665 Unlike</span>` 
                    : `<span class="plus" data-caseid="${d.case_id}">&#x2661 Like</span>`
                }
            </div>
            <div class="image-wrapper">
                <div class=""></div>
                <div class="image-container">
                    <a href="${d.web_url}"><img src="${d.image_path}"></a>
                </div>
            </div>
            <p class="entry">${d.entry}</p>
            <span class="tag"># ${d.category}</span>
            <span class="tag"># ${d.topic}</span>
        </div>
        `;
    }

    // Add event handlers after creating the HTML
    setTimeout(function() {
        // Handle click on selected items
        $('.remove').click(function() {
            var caseId = $(this).data('caseid');
            console.log('remove', caseId);
            $.post('/backend-api/remove_item', {case_id: caseId}, function(resultData) {
                var result = refreshResults(resultData);
                $('#result').html(result);
                var query_set = refreshQuery(resultData);
                $('#queryset').html(query_set);
            });
        });

        // Handle click on plus items
        $('.plus').click(function() {
            var caseId = $(this).data('caseid');
            console.log('add', caseId);
            $.post('/backend-api/add_item', {case_id: caseId}, function(resultData) {
                var result = refreshResults(resultData);
                $('#result').html(result);
                var query_set = refreshQuery(resultData);
                $('#queryset').html(query_set);
            });
        });
    }, 1000);

    return result;
}

function refreshQuery(resultData){
    var query_set = '';
    queries = resultData['query'];
    image_path = resultData['image_path'];
    if (image_path != null) {
        $('#query-thumbail').html('<img src="' + image_path + '">');
    }
    for (var i = 0; i < queries.length; i++) {
        query_set += `
            <div class="query">
                <p class="query-content">${queries[i].query}</p>
                <input type="range" min="0" max="1" step="0.01" value="${queries[i].weight}" class="slider" id="slider${i}">
            </div>
        `;
    }    
    return query_set;
}