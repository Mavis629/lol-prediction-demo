document.addEventListener("DOMContentLoaded", function () {
    const gamePhaseSelect = document.getElementById("game_phase");
    const earlyInputs = document.getElementById("early-inputs");
    const midInputs = document.getElementById("mid-inputs");
    const lateInputs = document.getElementById("late-inputs");

    function updatePhaseInputs() {
        // 先全部隐藏
        earlyInputs.style.display = "none";
        midInputs.style.display = "none";
        lateInputs.style.display = "none";

        // 清除所有输入框的 required
        document.querySelectorAll(".phase-inputs input").forEach(input => {
            input.removeAttribute("required");
        });

        // 当前阶段开启
        const phase = gamePhaseSelect.value;
        if (phase === "early") {
            earlyInputs.style.display = "block";
            earlyInputs.querySelectorAll("input").forEach(input => input.setAttribute("required", "required"));
        } else if (phase === "mid") {
            midInputs.style.display = "block";
            midInputs.querySelectorAll("input").forEach(input => input.setAttribute("required", "required"));
        } else if (phase === "late") {
            lateInputs.style.display = "block";
            lateInputs.querySelectorAll("input").forEach(input => input.setAttribute("required", "required"));
        }
    }

    gamePhaseSelect.addEventListener("change", updatePhaseInputs);
    updatePhaseInputs(); // 页面加载时初始化
});
