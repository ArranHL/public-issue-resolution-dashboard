function initStatistics() {
    const statsContainer = document.getElementById('statistics');
    statsContainer.innerHTML = '<h2>Statistics</h2><div id="stats-content"></div>';
  }
  
  function updateStatistics(issues) {
    const statsContent = document.getElementById('stats-content');
    const totalIssues = issues.length;
    const openIssues = issues.filter(issue => issue.state === 'open').length;
    const resolvedIssues = issues.filter(issue => issue.state === 'resolved').length;
  
    statsContent.innerHTML = `
        <p>Total Issues: ${totalIssues}</p>
        <p>Open Issues: ${openIssues}</p>
        <p>Resolved Issues: ${resolvedIssues}</p>
    `;
  }
  