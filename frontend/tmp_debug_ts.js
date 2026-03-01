const fs = require('fs');

const filtered = [
    {
        bncc_code: "EF06MA01",
        description: "description obj 1",
        status: "approved",
        has_rubrics: true,
        rubrics_status: "approved"
    },
    {
        bncc_code: "EF06MA01",
        description: "description obj 2",
        status: "approved",
        has_rubrics: true,
        rubrics_status: "approved"
    }
];

const groupedSkills = filtered.reduce((acc, curr) => {
    const code = curr.bncc_code || "Sem BNCC vinculada";
    if (!acc[code]) acc[code] = { description: curr.bncc_description || "", items: [] };
    acc[code].items.push(curr);
    return acc;
}, {});

const groupsArray = Object.entries(groupedSkills).map(([code, data]) => {
    let allStatuses = [];
    data.items.forEach((o) => {
        allStatuses.push(o.status);
        if (o.has_rubrics && o.rubrics_status) {
            allStatuses.push(o.rubrics_status);
        } else if (o.status === "approved" && !o.has_rubrics) {
            allStatuses.push("pending");
        }
    });

    let skillStatus = "draft";
    if (allStatuses.includes("rejected")) skillStatus = "rejected";
    else if (allStatuses.includes("pending")) skillStatus = "pending";
    else if (allStatuses.length > 0 && allStatuses.every(s => s === "approved")) skillStatus = "approved";

    return { code, skillStatus, allStatuses };
});

console.log(JSON.stringify(groupsArray, null, 2));
